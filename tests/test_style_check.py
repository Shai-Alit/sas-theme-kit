"""Tests for the style-only checker. No Streamlit needed."""

import shutil
import subprocess
from pathlib import Path

import pytest

from sas_theme.style_check import (
    Status,
    check_pair,
    check_python,
    check_requirements,
    check_streamlit_config,
    compare_git,
    compare_paths,
    _toml,
)

REPO = Path(__file__).resolve().parent.parent
UBER = REPO / "test_apps" / "nyc_uber"
HELLO = REPO / "test_apps" / "streamlit_hello"

ORIGINAL = """
import streamlit as st
st.set_page_config(page_title="X")
x = st.slider("n", 0, 10)
with st.sidebar:
    st.write(x * 2)
"""


def test_identical_is_ok():
    assert check_python("a.py", ORIGINAL, ORIGINAL).status is Status.OK


def test_adding_banner_footer_and_comments_is_ok():
    converted = """
import streamlit as st
from sas_theme import render_banner
from sas_theme.footer import render_footer
import sas_theme

# a new comment, and different formatting below
st.set_page_config( page_title = "X" )
render_banner(title="X", subtitle="y", variant="grey")
x = st.slider("n", 0, 10)
with st.sidebar:
    render_footer(text="t")
    st.write(x * 2)
sas_theme.render_footer()
"""
    r = check_python("a.py", ORIGINAL, converted)
    assert r.status is Status.OK, r.details
    assert "3 banner/footer call(s) added" in r.message


@pytest.mark.parametrize(
    "converted",
    [
        ORIGINAL.replace("0, 10", "0, 20"),                       # changed a value
        ORIGINAL + "st.button('new')\n",                          # added a widget
        ORIGINAL.replace("x * 2", "x * 3"),                       # changed logic
        ORIGINAL + "render_banner(title=load_title())\n",         # kit call that runs code
        ORIGINAL + "banner = render_banner(title='x')\n",         # not a plain statement
        ORIGINAL + "st.markdown('<style>h1{color:red}</style>', unsafe_allow_html=True)\n",
    ],
)
def test_other_changes_fail(converted):
    r = check_python("a.py", ORIGINAL, converted)
    assert r.status is Status.FAIL
    assert r.details  # includes a diff


def test_syntax_error_fails():
    assert check_python("a.py", ORIGINAL, "def (:\n").status is Status.FAIL


def test_mixed_import_keeps_other_names():
    orig = "import os\nprint(os.sep)\n"
    conv = "import os, sas_theme\nprint(os.sep)\nsas_theme.render_banner(title='t')\n"
    assert check_python("a.py", orig, conv).status is Status.OK


def test_new_and_deleted_python_files_fail():
    assert check_pair("new.py", None, "print(1)").status is Status.FAIL
    assert check_pair("old.py", "print(1)", None).status is Status.FAIL


def test_requirements_rules():
    assert check_requirements("requirements.txt", "pandas\n", "pandas\nsas-theme-kit==0.3.0\n").status is Status.OK
    assert check_requirements("requirements.txt", "pandas\n", "pandas\nrequests\n").status is Status.REVIEW
    assert check_requirements("requirements.txt", "pandas\n", "").status is Status.REVIEW


@pytest.mark.skipif(_toml is None, reason="needs tomllib (3.11+) or tomli")
def test_config_only_theme_may_change():
    old = '[server]\nport = 8501\n[theme]\nprimaryColor = "#f00"\n'
    ok = '[server]\nport = 8501\n[theme]\nbase = "x.toml"\n'
    bad = '[server]\nport = 9999\n[theme]\nbase = "x.toml"\n'
    assert check_streamlit_config(".streamlit/config.toml", old, ok).status is Status.OK
    assert check_streamlit_config(".streamlit/config.toml", old, bad).status is Status.FAIL
    assert check_streamlit_config(".streamlit/config.toml", None, '[theme]\nbase="x"\n').status is Status.OK


# --- The shipped test apps -------------------------------------------------


def test_shipped_uber_conversion_passes():
    report = compare_paths(UBER / "streamlit_app.py", UBER / "streamlit_app_sas.py")
    assert not report.failed, report.format()


def test_shipped_bad_conversion_is_caught():
    report = compare_paths(UBER / "streamlit_app.py", UBER / "streamlit_app_bad_conversion.py")
    assert report.failed
    diff = "\n".join(report.results[0].details)
    assert "nrows=50000" in diff and "#0766D1" in diff


def test_shipped_hello_conversion_passes():
    report = compare_paths(HELLO / "streamlit_app.py", HELLO / "streamlit_app_sas.py")
    assert not report.failed, report.format()


def test_directory_mode(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    shutil.copytree(UBER, a)
    shutil.copytree(UBER, b)
    (b / "streamlit_app.py").write_text((UBER / "streamlit_app_sas.py").read_text())
    report = compare_paths(a, b)
    assert not report.failed, report.format()
    (b / "extra.py").write_text("print('new logic')\n")
    assert compare_paths(a, b).failed


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_git_mode(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "app.py").write_text(ORIGINAL)
    git("add", ".")
    git("commit", "-qm", "base")

    (tmp_path / "app.py").write_text("from sas_theme import render_banner\n" + ORIGINAL
                                     + "render_banner(title='x')\n")
    assert not compare_git("HEAD", tmp_path).failed

    (tmp_path / "helper.py").write_text("x = 1\n")  # untracked new code
    report = compare_git("HEAD", tmp_path)
    assert report.failed
    assert any(r.path == "helper.py" and r.status is Status.FAIL for r in report.results)
