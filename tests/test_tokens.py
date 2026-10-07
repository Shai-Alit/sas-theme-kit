"""The theme TOML and the CSS tokens must agree, and colors must stay accessible."""

import re

import pytest

from sas_theme.paths import THEME_FILE, TOKENS_CSS
from sas_theme.style_check import _toml

pytestmark = pytest.mark.skipif(_toml is None, reason="needs tomllib (3.11+) or tomli")

TOML_TO_CSS = {
    "primaryColor": "--sas-primary",
    "backgroundColor": "--sas-background",
    "secondaryBackgroundColor": "--sas-secondary-background",
    "textColor": "--sas-text",
    "linkColor": "--sas-link",
    "borderColor": "--sas-border",
}


def _theme():
    return _toml.loads(THEME_FILE.read_text(encoding="utf-8"))["theme"]


def _css_vars():
    return {m[0]: m[1].upper() for m in
            re.findall(r"(--sas-[a-z-]+):\s*(#[0-9A-Fa-f]{6})", TOKENS_CSS.read_text())}


def _contrast(a: str, b: str) -> float:
    def lum(h):
        rgb = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_theme_file_is_valid_and_light_based():
    theme = _theme()
    assert theme["base"] == "light"
    for key in TOML_TO_CSS:
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", theme[key]), key


def test_css_tokens_match_theme():
    theme, css = _theme(), _css_vars()
    for key, var in TOML_TO_CSS.items():
        assert css[var] == theme[key].upper(), f"{var} != theme.{key}"


def test_chart_palette_is_in_tokens():
    palette = {c.upper() for c in _theme()["chartCategoricalColors"]}
    assert palette <= set(_css_vars().values())


def test_text_contrast_meets_wcag_aa():
    t = _theme()
    assert _contrast(t["textColor"], t["backgroundColor"]) >= 4.5
    assert _contrast(t["textColor"], t["secondaryBackgroundColor"]) >= 4.5
    assert _contrast(t["linkColor"], t["backgroundColor"]) >= 4.5
    assert _contrast(_css_vars()["--sas-muted-text"], t["secondaryBackgroundColor"]) >= 4.5
