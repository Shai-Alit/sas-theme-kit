"""Banner, footer and asset tests. These need Streamlit installed."""

import os
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from sas_theme._assets import encode_image_as_data_uri  # noqa: E402
from sas_theme.paths import LOGO_BLUE, LOGO_WHITE, PLACEHOLDER_LOGO  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def _render(fn_source: str) -> AppTest:
    """Run a tiny script through Streamlit's test harness and return it."""
    at = AppTest.from_string(fn_source)
    at.run(timeout=10)
    assert not at.exception, at.exception
    return at


def _html(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


# --- assets ----------------------------------------------------------------


def test_bundled_assets_exist():
    for p in (LOGO_BLUE, LOGO_WHITE, PLACEHOLDER_LOGO):
        assert p.is_file(), p


def test_encode_image(tmp_path):
    assert encode_image_as_data_uri(PLACEHOLDER_LOGO).startswith("data:image/svg+xml;base64,")
    assert encode_image_as_data_uri(tmp_path / "missing.svg") is None
    bmp = tmp_path / "logo.bmp"
    bmp.write_bytes(b"x")
    assert encode_image_as_data_uri(bmp) is None


# --- banner ----------------------------------------------------------------


def test_banner_default():
    html = _html(_render("from sas_theme import render_banner\nrender_banner(title='Hi <b>')"))
    assert "sas-theme-banner--blue" in html
    assert "Hi &lt;b&gt;" in html  # escaped
    assert "data:image/svg+xml" in html  # bundled logo


def test_banner_grey_no_logo():
    html = _html(_render(
        "from sas_theme import render_banner\n"
        "render_banner(title='S', subtitle='sub', variant='grey', logo_path=None)"
    ))
    assert "sas-theme-banner--grey" in html and "<img" not in html


def test_banner_never_raises():
    html = _html(_render(
        "from sas_theme import render_banner\n"
        "render_banner(title='x', variant='purple', logo_path='/no/such/file.svg')"
    ))
    assert "sas-theme-banner--blue" in html  # fell back


# --- footer ----------------------------------------------------------------


def test_footer_default_and_text():
    html = _html(_render("from sas_theme import render_footer\nrender_footer(text='a & b')"))
    assert "sas-theme-footer" in html and "a &amp; b" in html and "<img" in html


def test_footer_nothing_to_show_renders_nothing():
    at = _render("from sas_theme import render_footer\nrender_footer(logo_path=None)")
    assert len(at.markdown) == 0


def test_footer_rejects_javascript_links():
    html = _html(_render(
        "from sas_theme import render_footer\n"
        "render_footer(link_url='javascript:alert(1)')"
    ))
    assert "javascript:" not in html and "<a " not in html


# --- whole apps ------------------------------------------------------------


def test_gallery_app_runs():
    at = AppTest.from_file(str(REPO / "examples" / "gallery_app.py"))
    at.run(timeout=30)
    assert not at.exception


@pytest.mark.skipif(not os.environ.get("SAS_THEME_NETWORK_TESTS"),
                    reason="downloads demo data; set SAS_THEME_NETWORK_TESTS=1")
@pytest.mark.parametrize("script", ["streamlit_app.py", "streamlit_app_sas.py"])
def test_uber_app_runs(script):
    at = AppTest.from_file(str(REPO / "test_apps" / "nyc_uber" / script))
    at.run(timeout=120)
    assert not at.exception
