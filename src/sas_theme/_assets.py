"""Shared helper for encoding local image assets as data: URIs."""

from __future__ import annotations

import base64
import functools
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MIME_BY_SUFFIX = {
    "svg": "svg+xml",
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "gif": "gif",
    "webp": "webp",
}


def encode_image_as_data_uri(path: Path) -> str | None:
    """Read an image file and return it as a base64 data: URI, or None on failure.

    Results are cached per (path, modified-time), because Streamlit reruns
    the whole script on every interaction and the logo never changes.
    """
    path = Path(path)
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as exc:
        logger.warning("sas_theme: could not read image at %s (%s)", path, exc)
        return None
    return _encode_cached(str(path), mtime)


@functools.lru_cache(maxsize=32)
def _encode_cached(path_str: str, _mtime_ns: int) -> str | None:
    path = Path(path_str)
    suffix = path.suffix.lower().lstrip(".")
    mime = _MIME_BY_SUFFIX.get(suffix)
    if mime is None:
        logger.warning(
            "sas_theme: unsupported image file type '%s' at %s. Supported types: %s",
            suffix,
            path,
            ", ".join(sorted(_MIME_BY_SUFFIX)),
        )
        return None
    try:
        data = path.read_bytes()
    except OSError as exc:
        logger.warning("sas_theme: could not read image at %s (%s)", path, exc)
        return None
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"
