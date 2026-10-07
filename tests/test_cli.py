"""CLI tests that don't launch Streamlit."""

import sys
from pathlib import Path

import pytest

from sas_theme import cli
from sas_theme.paths import THEME_FILE
from sas_theme.style_check import _toml

REPO = Path(__file__).resolve().parent.parent


def test_run_command_adds_theme_base_before_app():
    cmd = cli.build_run_command("app.py", ["--server.port", "8502", "--", "--my-arg"])
    assert cmd[:4] == [sys.executable, "-m", "streamlit", "run"]
    assert cmd[4] == f"--theme.base={THEME_FILE}"
    assert cmd[5:] == ["app.py", "--server.port", "8502", "--", "--my-arg"]


def test_run_command_respects_user_theme_base():
    cmd = cli.build_run_command("app.py", ["--theme.base=dark"])
    assert not any(str(THEME_FILE) in c for c in cmd)


def test_env_var_conflicts(tmp_path):
    found = cli.theme_conflicts(tmp_path, {"STREAMLIT_THEME_PRIMARY_COLOR": "#f00",
                                           "STREAMLIT_THEME_BASE": "light",
                                           "PATH": "/bin"})
    assert found == ["environment variable STREAMLIT_THEME_PRIMARY_COLOR"]


@pytest.mark.skipif(_toml is None, reason="needs tomllib (3.11+) or tomli")
def test_legacy_app_config_conflicts_are_reported():
    found = cli.theme_conflicts(REPO / "test_apps" / "legacy_conflict", {})
    assert any("primaryColor" in f for f in found)
    assert any("secondaryBackgroundColor" in f for f in found)


def test_theme_path_command(capsys):
    assert cli.main(["theme-path"]) == 0
    assert Path(capsys.readouterr().out.strip()) == THEME_FILE
    assert THEME_FILE.is_file()


def test_check_command_exit_codes(capsys):
    uber = REPO / "test_apps" / "nyc_uber"
    good = cli.main(["check", str(uber / "streamlit_app.py"), str(uber / "streamlit_app_sas.py")])
    bad = cli.main(["check", str(uber / "streamlit_app.py"),
                    str(uber / "streamlit_app_bad_conversion.py")])
    assert (good, bad) == (0, 1)


def test_run_missing_app_returns_error(tmp_path):
    assert cli.main(["run", str(tmp_path / "nope.py")]) == 2
