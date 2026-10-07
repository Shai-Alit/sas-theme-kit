"""``sas-theme`` command-line tool.

    sas-theme run APP.py [streamlit options] [-- script args]
        Run any Streamlit app with the SAS theme, without editing it.

    sas-theme check ORIGINAL CONVERTED      (two files or two folders)
    sas-theme check --against REF [PATH...] (git working tree vs REF)
        Verify a conversion changed styling only.

    sas-theme theme-path | tokens-path | version
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .paths import THEME_FILE, TOKENS_CSS


def _load_toml(path: Path) -> dict | None:
    from .style_check import _toml

    if _toml is None or not path.is_file():
        return None
    try:
        return _toml.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def theme_conflicts(cwd: Path, environ: dict[str, str] | None = None) -> list[str]:
    """Theme settings that would override the SAS theme for an app run from ``cwd``.

    Streamlit reads ``$CWD/.streamlit/config.toml`` (not the app's folder), and
    any ``[theme]`` key there wins over the base theme file. Env vars do too.
    """
    environ = dict(os.environ if environ is None else environ)
    found: list[str] = []
    cfg = _load_toml(cwd / ".streamlit" / "config.toml")
    if cfg:
        for key, value in (cfg.get("theme") or {}).items():
            if key == "base":
                continue  # our --theme.base flag takes precedence over this
            if isinstance(value, dict):
                found.append(f".streamlit/config.toml [theme.{key}] section")
            else:
                found.append(f".streamlit/config.toml theme.{key} = {value!r}")
    for name in sorted(environ):
        if name.startswith("STREAMLIT_THEME_") and name != "STREAMLIT_THEME_BASE":
            found.append(f"environment variable {name}")
    return found


def build_run_command(app: str, extra: list[str]) -> list[str]:
    cmd = [sys.executable, "-m", "streamlit", "run"]
    if not any(a == "--theme.base" or a.startswith("--theme.base=") for a in extra):
        cmd.append(f"--theme.base={THEME_FILE}")
    return cmd + [app, *extra]


def _cmd_run(args: argparse.Namespace) -> int:
    app = Path(args.app)
    if not app.is_file():
        print(f"sas-theme: app file not found: {app}", file=sys.stderr)
        return 2
    conflicts = theme_conflicts(Path.cwd())
    if conflicts:
        print("sas-theme: WARNING: these settings will override parts of the SAS theme:",
              file=sys.stderr)
        for c in conflicts:
            print(f"    - {c}", file=sys.stderr)
        print("  Remove them (or run from a different folder) for the full SAS look.\n",
              file=sys.stderr)
    cmd = build_run_command(str(app), list(args.streamlit_args))
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130


def _cmd_check(args: argparse.Namespace) -> int:
    from .style_check import compare_git, compare_paths

    if args.against:
        report = compare_git(args.against, Path(args.repo), args.paths)
    else:
        if len(args.paths) != 2:
            print("usage: sas-theme check ORIGINAL CONVERTED  |  sas-theme check --against REF",
                  file=sys.stderr)
            return 2
        report = compare_paths(Path(args.paths[0]), Path(args.paths[1]))
    print(report.format())
    return report.exit_code(strict=args.strict)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sas-theme", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run a Streamlit app with the SAS theme (no code changes)")
    p_run.add_argument("app")
    p_run.add_argument("streamlit_args", nargs=argparse.REMAINDER,
                       help="passed through to `streamlit run`")
    p_run.set_defaults(func=_cmd_run)

    p_check = sub.add_parser("check", help="verify a conversion changed styling only")
    p_check.add_argument("paths", nargs="*")
    p_check.add_argument("--against", metavar="REF",
                         help="compare the git working tree with this ref (e.g. main)")
    p_check.add_argument("--repo", default=".", help="git repo folder (with --against)")
    p_check.add_argument("--strict", action="store_true",
                         help="also fail on files that only need review")
    p_check.set_defaults(func=_cmd_check)

    for name, path in (("theme-path", THEME_FILE), ("tokens-path", TOKENS_CSS)):
        p = sub.add_parser(name, help=f"print the path of the bundled {path.name}")
        p.set_defaults(func=lambda _a, _p=path: print(_p) or 0)

    p_ver = sub.add_parser("version", help="print the kit version")
    p_ver.set_defaults(func=lambda _a: print(__version__) or 0)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
