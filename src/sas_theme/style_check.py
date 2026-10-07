"""Verify that converting an app to the SAS theme changed styling only.

The rule this enforces:

* **Python files**: after removing ``sas_theme`` imports and plain
  ``render_banner(...)`` / ``render_footer(...)`` statements, the code must
  be *identical* to the original (compared as syntax trees, so whitespace,
  comments and formatting changes are ignored). The removed calls may only
  take literal or simple-name arguments, nothing that calls a function.
* **.streamlit/config.toml**: only the ``[theme]`` table may differ.
* **requirements*.txt**: only lines adding ``sas-theme-kit`` may be added.
* **Anything else** (new/deleted/renamed Python files, other files) is
  flagged for human review.

This doesn't import Streamlit, so it runs in a bare CI job.

Usage (also available as ``sas-theme check``)::

    sas-theme check ORIGINAL CONVERTED          # two files or two folders
    sas-theme check --against main              # git working tree vs a ref
"""

from __future__ import annotations

import ast
import difflib
import enum
import fnmatch
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

try:  # Python 3.11+
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - depends on interpreter
    try:
        import tomli as _toml  # type: ignore[no-redef]
    except ModuleNotFoundError:
        _toml = None  # type: ignore[assignment]

KIT_MODULE = "sas_theme"
KIT_CALLS = frozenset({"render_banner", "render_footer"})
IGNORED_DIRS = {".git", "__pycache__", ".venv", "venv", "env", ".mypy_cache",
                ".pytest_cache", "node_modules", "build", "dist", ".ruff_cache"}
_REQ_KIT_LINE = re.compile(r"^\s*sas[-_.]theme[-_.]kit\b", re.IGNORECASE)


class Status(enum.Enum):
    OK = "ok"
    REVIEW = "review"
    FAIL = "fail"


@dataclass
class FileResult:
    path: str
    status: Status
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class Report:
    results: list[FileResult] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(r.status is Status.FAIL for r in self.results)

    @property
    def needs_review(self) -> bool:
        return any(r.status is Status.REVIEW for r in self.results)

    def exit_code(self, strict: bool = False) -> int:
        if self.failed or (strict and self.needs_review):
            return 1
        return 0

    def format(self) -> str:
        if not self.results:
            return "No changed files found. Nothing to check."
        icon = {Status.OK: "PASS  ", Status.REVIEW: "REVIEW", Status.FAIL: "FAIL  "}
        lines = []
        for r in sorted(self.results, key=lambda r: (r.status is Status.OK, r.path)):
            lines.append(f"[{icon[r.status]}] {r.path}: {r.message}")
            lines.extend(f"         {d}" for d in r.details)
        n = {s: sum(r.status is s for r in self.results) for s in Status}
        lines.append("")
        lines.append(
            f"{n[Status.OK]} passed, {n[Status.REVIEW]} need review, {n[Status.FAIL]} failed."
        )
        if self.failed:
            lines.append("Result: NOT style-only. Logic or structure changed (see FAIL lines).")
        elif self.needs_review:
            lines.append("Result: style-only for all Python code; some files need a human look.")
        else:
            lines.append("Result: style-only. No logic changes detected.")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Python: syntax-tree comparison with kit calls removed
# --------------------------------------------------------------------------


def _is_simple_expr(node: ast.AST) -> bool:
    """True if evaluating ``node`` can't run user code (no calls etc.)."""
    for sub in ast.walk(node):
        if isinstance(sub, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom,
                            ast.NamedExpr, ast.Lambda)):
            return False
    return True


def _is_kit_call(stmt: ast.stmt) -> bool:
    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)):
        return False
    call = stmt.value
    func = call.func
    name = func.id if isinstance(func, ast.Name) else (
        func.attr if isinstance(func, ast.Attribute) else None
    )
    if name not in KIT_CALLS:
        return False
    if isinstance(func, ast.Attribute) and not _is_simple_expr(func.value):
        return False
    args = list(call.args) + [kw.value for kw in call.keywords]
    return all(_is_simple_expr(a) for a in args)


def _strip_kit_import(stmt: ast.stmt) -> ast.stmt | None:
    """Return the statement with sas_theme imports removed (None if nothing left)."""
    if isinstance(stmt, ast.ImportFrom) and stmt.level == 0 and stmt.module and (
        stmt.module == KIT_MODULE or stmt.module.startswith(KIT_MODULE + ".")
    ):
        return None
    if isinstance(stmt, ast.Import):
        kept = [a for a in stmt.names
                if not (a.name == KIT_MODULE or a.name.startswith(KIT_MODULE + "."))]
        if not kept:
            return None
        if len(kept) != len(stmt.names):
            return ast.Import(names=kept)
    return stmt


class _KitStripper(ast.NodeTransformer):
    def generic_visit(self, node: ast.AST) -> ast.AST:
        for name, value in ast.iter_fields(node):
            if isinstance(value, list) and value and all(isinstance(v, ast.stmt) for v in value):
                new_body: list[ast.stmt] = []
                for stmt in value:
                    if _is_kit_call(stmt):
                        continue
                    stripped = _strip_kit_import(stmt)
                    if stripped is None:
                        continue
                    new_body.append(self.visit(stripped))
                setattr(node, name, new_body)
            elif isinstance(value, list):
                setattr(node, name, [self.visit(v) if isinstance(v, ast.AST) else v
                                     for v in value])
            elif isinstance(value, ast.AST):
                setattr(node, name, self.visit(value))
        return node


def _normalized(source: str) -> ast.Module:
    return _KitStripper().visit(ast.parse(source))


def _count_kit_calls(tree: ast.AST) -> int:
    return sum(1 for n in ast.walk(tree) if isinstance(n, ast.stmt) and _is_kit_call(n))


def _unparse_lines(tree: ast.AST) -> list[str]:
    try:
        return ast.unparse(tree).splitlines()  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - unparse is best effort
        return ast.dump(tree, indent=1).splitlines()


def check_python(path: str, original: str, converted: str) -> FileResult:
    try:
        before = _normalized(original)
    except SyntaxError as exc:
        return FileResult(path, Status.REVIEW, f"original doesn't parse ({exc.msg}); can't verify")
    try:
        after_raw = ast.parse(converted)
        after = _normalized(converted)
    except SyntaxError as exc:
        return FileResult(path, Status.FAIL, f"converted file has a syntax error: {exc}")

    if ast.dump(before) == ast.dump(after):
        added = _count_kit_calls(after_raw) - _count_kit_calls(ast.parse(original))
        what = f"{added} banner/footer call(s) added" if added > 0 else "no code changes"
        return FileResult(path, Status.OK, f"style-only ({what})")

    diff = list(difflib.unified_diff(
        _unparse_lines(before), _unparse_lines(after),
        "original (kit calls removed)", "converted (kit calls removed)", lineterm="", n=1,
    ))
    if len(diff) > 40:
        diff = diff[:40] + [f"... ({len(diff) - 40} more diff lines)"]
    return FileResult(path, Status.FAIL, "code changed beyond adding sas_theme calls", diff)


# --------------------------------------------------------------------------
# Config, requirements, everything else
# --------------------------------------------------------------------------


def check_streamlit_config(path: str, original: str | None, converted: str) -> FileResult:
    if _toml is None:
        return FileResult(path, Status.REVIEW,
                          "can't parse TOML on this Python (<3.11 without 'tomli'); check by hand")
    try:
        new = _toml.loads(converted)
        old = _toml.loads(original) if original is not None else {}
    except Exception as exc:  # noqa: BLE001
        return FileResult(path, Status.FAIL, f"invalid TOML: {exc}")
    old.pop("theme", None)
    new.pop("theme", None)
    if old == new:
        return FileResult(path, Status.OK, "only the [theme] table changed")
    changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    return FileResult(path, Status.FAIL,
                      "non-theme settings changed: " + ", ".join(f"[{k}]" for k in changed))


def check_requirements(path: str, original: str | None, converted: str) -> FileResult:
    def lines(text: str | None) -> list[str]:
        return [ln.strip() for ln in (text or "").splitlines()
                if ln.strip() and not ln.strip().startswith("#")]

    old, new = lines(original), lines(converted)
    added = [ln for ln in new if ln not in old]
    removed = [ln for ln in old if ln not in new]
    other = [ln for ln in added if not _REQ_KIT_LINE.match(ln) and "sas-theme-kit" not in ln]
    if not removed and not other:
        return FileResult(path, Status.OK, "only sas-theme-kit added" if added else "unchanged")
    details = [f"+ {ln}" for ln in other] + [f"- {ln}" for ln in removed]
    return FileResult(path, Status.REVIEW, "dependencies changed beyond adding sas-theme-kit",
                      details)


def check_pair(path: str, original: str | None, converted: str | None) -> FileResult:
    """Classify one file change. ``None`` means the file doesn't exist on that side."""
    name = Path(path).name
    if original is not None and converted is not None and original == converted:
        return FileResult(path, Status.OK, "unchanged")
    if converted is None:
        return FileResult(path, Status.FAIL, "file was deleted")
    if path.replace("\\", "/").endswith(".streamlit/config.toml"):
        return check_streamlit_config(path, original, converted)
    if fnmatch.fnmatch(name, "requirements*.txt"):
        return check_requirements(path, original, converted)
    if name.endswith(".py"):
        if original is None:
            return FileResult(path, Status.FAIL, "new Python file added (new code, not styling)")
        return check_python(path, original, converted)
    if original is None:
        return FileResult(path, Status.REVIEW, "new non-Python file; check it's styling-related")
    return FileResult(path, Status.REVIEW, "non-Python file changed; check by hand")


# --------------------------------------------------------------------------
# Sources of file pairs
# --------------------------------------------------------------------------


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _walk(root: Path) -> Iterator[str]:
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts[:-1]) & IGNORED_DIRS) \
                and p.suffix not in {".pyc", ".pyo"}:
            yield p.relative_to(root).as_posix()


def compare_paths(original: Path, converted: Path) -> Report:
    """Compare two files, or two directories file-by-file."""
    report = Report()
    if original.is_file() and converted.is_file():
        report.results.append(check_pair(converted.name, _read(original), _read(converted)))
        return report
    if not (original.is_dir() and converted.is_dir()):
        raise ValueError("pass two files or two directories")
    rels = sorted(set(_walk(original)) | set(_walk(converted)))
    for rel in rels:
        a, b = original / rel, converted / rel
        report.results.append(check_pair(
            rel, _read(a) if a.is_file() else None, _read(b) if b.is_file() else None
        ))
    return report


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout


def compare_git(ref: str, repo: Path = Path("."), paths: Iterable[str] = ()) -> Report:
    """Compare the working tree (including uncommitted/untracked files) to ``ref``."""
    report = Report()
    top = Path(_git(repo, "rev-parse", "--show-toplevel").strip())
    pathspec = ["--", *paths] if paths else []
    changes: list[tuple[str, str]] = []
    for line in _git(top, "diff", "--name-status", "-M", ref, *pathspec).splitlines():
        parts = line.split("\t")
        changes.append((parts[0][0], parts[-1]))
        if parts[0].startswith("R"):
            report.results.append(FileResult(parts[1], Status.FAIL,
                                             f"file renamed to {parts[-1]}"))
            changes[-1] = ("A", parts[-1])
    for rel in _git(top, "ls-files", "--others", "--exclude-standard", *pathspec).splitlines():
        changes.append(("A", rel))

    for kind, rel in changes:
        new_path = top / rel
        converted = _read(new_path) if new_path.is_file() else None
        original = None
        if kind != "A":
            try:
                original = _git(top, "show", f"{ref}:{rel}")
            except subprocess.CalledProcessError:
                original = None
        report.results.append(check_pair(rel, original, converted))
    return report
