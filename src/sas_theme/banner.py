"""A full-width color banner for Streamlit apps.

Mirrors the approved SAS template's cover/section slides: a solid SAS Blue
(or Slate) block with white text and the white SAS logo.

This is purely presentational: it renders HTML through ``st.markdown`` and
creates no widgets, session state, or callbacks, so adding it cannot change
an app's behavior.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

import streamlit as st

from ._assets import encode_image_as_data_uri
from .paths import LOGO_WHITE

logger = logging.getLogger(__name__)

# "blue" = SAS Blue, the template's primary color.
# "grey" = Slate, the template's alternate section-divider color.
_VARIANTS = ("blue", "grey")

# One rule per variant (rather than interpolating the color into a shared
# class) so two banners with different variants on one page don't fight.
#
# Accessibility (WCAG 2.1 AA):
#   white on SAS Blue #0766D1 = 5.5:1, which passes for all text.
#   white on Slate   #7D879A = 3.6:1, which passes only for "large" text
#   (>= 24px, or >= 18.66px bold). So on the grey variant the subtitle is
#   rendered at 1.2rem bold to stay in the large-text bracket, and no text
#   uses reduced opacity.
_BANNER_CSS = """
<style>
.sas-theme-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
    padding: 2rem;
    margin-bottom: 1.5rem;
    border-radius: 0.5rem;
    color: #FFFFFF;
}
.sas-theme-banner--blue { background-color: #0766D1; }
.sas-theme-banner--grey { background-color: #7D879A; }
.sas-theme-banner .sas-theme-banner__title {
    margin: 0;
    padding: 0;
    font-size: 1.75rem;
    font-weight: 700;
    line-height: 1.25;
    color: #FFFFFF;
}
.sas-theme-banner .sas-theme-banner__subtitle {
    margin: 0.25rem 0 0;
    font-size: 1rem;
    color: #FFFFFF;
}
.sas-theme-banner--grey .sas-theme-banner__subtitle {
    font-size: 1.2rem;
    font-weight: 700;
}
.sas-theme-banner img {
    display: block;
    max-width: 100%;
}
</style>
"""


def render_banner(
    title: str,
    subtitle: str | None = None,
    variant: str = "blue",
    logo_path: str | Path | None = LOGO_WHITE,
    logo_alt: str = "SAS",
    logo_height_px: int = 40,
) -> None:
    """Render a full-width color banner, SAS-template style.

    Never raises: bad inputs are logged and the banner degrades gracefully,
    because a styling helper should never be able to take an app down.

    Args:
        title: Banner heading (plain text; HTML-escaped).
        subtitle: Optional line under the title (plain text; HTML-escaped).
        variant: "blue" (default) or "grey". Unknown values log a warning
            and fall back to "blue".
        logo_path: Logo shown at the right. Defaults to the bundled white
            SAS logo. ``None`` hides it. Missing/unreadable files log a
            warning and the banner renders without a logo.
        logo_alt: Accessible alt text for the logo.
        logo_height_px: Rendered logo height in pixels.
    """
    if variant not in _VARIANTS:
        logger.warning(
            "sas_theme.banner: unknown variant %r (expected one of %s); using 'blue'.",
            variant,
            _VARIANTS,
        )
        variant = "blue"

    logo_html = ""
    if logo_path is not None:
        resolved = Path(logo_path)
        if resolved.is_file():
            data_uri = encode_image_as_data_uri(resolved)
            if data_uri:
                logo_html = (
                    f'<img src="{data_uri}" alt="{html.escape(logo_alt)}" '
                    f'height="{int(logo_height_px)}" />'
                )
        else:
            logger.warning(
                "sas_theme.banner: logo_path '%s' not found; rendering without a logo.",
                resolved,
            )

    subtitle_html = (
        f'<p class="sas-theme-banner__subtitle">{html.escape(subtitle)}</p>'
        if subtitle
        else ""
    )

    # A <div role="heading"> rather than <h1>: Streamlit decorates real
    # markdown headings with hover anchor links and its own heading CSS,
    # which we don't want inside the banner. role/aria-level keep it a
    # level-1 heading for screen readers.
    st.markdown(
        _BANNER_CSS
        + f'<div class="sas-theme-banner sas-theme-banner--{variant}">'
        f'<div><div class="sas-theme-banner__title" role="heading" aria-level="1">'
        f"{html.escape(title)}</div>{subtitle_html}</div>"
        f"{logo_html}"
        f"</div>",
        unsafe_allow_html=True,
    )
