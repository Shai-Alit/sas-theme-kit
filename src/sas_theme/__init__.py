"""SAS theme kit: SAS look-and-feel for Streamlit apps, without touching app logic.

``render_banner`` and ``render_footer`` are imported lazily so that the
``sas-theme`` CLI (``run`` / ``check`` / ``theme-path``) starts quickly and
the style checker works even where Streamlit isn't installed (e.g. CI).
"""

from __future__ import annotations

from typing import Any

try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("sas-theme-kit")
    except PackageNotFoundError:  # running from a source checkout
        __version__ = "0+unknown"
except ImportError:  # pragma: no cover
    __version__ = "0+unknown"

__all__ = ["render_banner", "render_footer", "__version__"]


def __getattr__(name: str) -> Any:
    if name == "render_banner":
        from .banner import render_banner

        return render_banner
    if name == "render_footer":
        from .footer import render_footer

        return render_footer
    raise AttributeError(f"module 'sas_theme' has no attribute {name!r}")
