"""Paths to files bundled inside the sas_theme package.

Everything lives inside the package so a plain ``pip install`` gives an app
the theme, the logos, and the tokens; nothing needs copying.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
_ASSET_ROOT = PACKAGE_ROOT / "assets"

THEME_FILE = PACKAGE_ROOT / "themes" / "sas-light.toml"
"""Streamlit theme file. Use as ``[theme] base`` or via ``sas-theme run``."""

TOKENS_CSS = PACKAGE_ROOT / "tokens" / "sas-tokens.css"
"""The same colors as CSS custom properties, for non-Streamlit apps."""

LOGO_BLUE = _ASSET_ROOT / "sas-brand" / "sas_logo_blue.svg"
"""Full "swirl + sas" lockup, SAS Blue: for white/light backgrounds."""

LOGO_WHITE = _ASSET_ROOT / "sas-brand" / "sas_logo_white.svg"
"""Full "swirl + sas" lockup, white: for dark/solid-color backgrounds."""

PLACEHOLDER_LOGO = _ASSET_ROOT / "placeholder-logo.svg"
"""Generic, non-SAS placeholder: for testing layout only."""
