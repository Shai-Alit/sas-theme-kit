"""A small footer (logo and/or text) for the bottom of a Streamlit page.

Purely presentational: renders HTML through ``st.markdown`` and creates no
widgets, session state, or callbacks.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

import streamlit as st

from ._assets import encode_image_as_data_uri
from .paths import LOGO_BLUE

logger = logging.getLogger(__name__)

_SAFE_URL_PREFIXES = ("https://", "http://", "mailto:")

# Text color #5A6170: 6.2:1 on white and 5.5:1 on #F0F1F4, which passes
# WCAG AA. (v0.2 used semi-transparent grey at about 3.3:1, which failed.)
# Tuned for the light SAS theme; the kit doesn't ship a dark theme.
_FOOTER_CSS = """
<style>
.sas-theme-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    flex-wrap: wrap;
    padding: 0.75rem 0.5rem;
    margin-top: 2rem;
    border-top: 1px solid #B9C0C8;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #5A6170;
    text-align: center;
}
.sas-theme-footer img {
    display: block;
    max-width: 100%;
}
.sas-theme-footer a {
    color: inherit;
    text-decoration: underline;
}
</style>
"""


def render_footer(
    logo_path: str | Path | None = LOGO_BLUE,
    alt_text: str = "SAS",
    link_url: str | None = None,
    height_px: int = 24,
    text: str | None = None,
) -> None:
    """Render a small footer with an optional logo and/or text.

    Never raises. If there's nothing to show (no logo, no text), renders
    nothing.

    Args:
        logo_path: Logo file (svg, png, jpg, gif, webp). Defaults to the
            bundled blue SAS logo. ``None`` hides it. Missing files log a
            warning and the footer renders without a logo.
        alt_text: Accessible alt text for the logo.
        link_url: If given, the logo links here (opens in a new tab).
        height_px: Logo height in pixels; width scales automatically.
        text: Optional short plain text (HTML-escaped), e.g. a disclaimer.
    """
    logo_html = ""
    if logo_path is not None:
        resolved = Path(logo_path)
        if resolved.is_file():
            data_uri = encode_image_as_data_uri(resolved)
            if data_uri:
                img_html = (
                    f'<img src="{data_uri}" alt="{html.escape(alt_text)}" '
                    f'height="{int(height_px)}" />'
                )
                if link_url and not link_url.lower().startswith(_SAFE_URL_PREFIXES):
                    logger.warning(
                        "sas_theme.footer: ignoring link_url %r (only http(s)/mailto allowed).",
                        link_url,
                    )
                    link_url = None
                if link_url:
                    logo_html = (
                        f'<a href="{html.escape(link_url)}" target="_blank" '
                        f'rel="noopener noreferrer">{img_html}</a>'
                    )
                else:
                    logo_html = img_html
        else:
            logger.warning(
                "sas_theme.footer: logo_path '%s' not found; rendering without a logo.",
                resolved,
            )

    text_html = f"<span>{html.escape(text)}</span>" if text else ""

    if not logo_html and not text_html:
        return

    st.markdown(
        _FOOTER_CSS
        + f'<div class="sas-theme-footer" role="contentinfo">{logo_html}{text_html}</div>',
        unsafe_allow_html=True,
    )
