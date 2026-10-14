"""Glossary of Surya Siddhanta terms for the React side panel.

The document is a single JSON file shipped with the package, read once per
process and served verbatim with a strong ETag so browsers revalidate
cheaply. Diagrams are hand-written SVGs served from a fixed directory; the
name pattern admits nothing but ``[a-z0-9-]+.svg``, so no request can reach
a file outside it.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

#: Package data directory holding the glossary and its diagrams.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
#: The glossary document.
GLOSSARY_PATH = DATA_DIR / "glossary.json"
#: Directory of popup diagrams.
IMAGE_DIR = DATA_DIR / "glossary_img"

_IMAGE_NAME = re.compile(r"[a-z0-9-]+\.svg")
_CACHE_HEADERS = {"Cache-Control": "public, max-age=3600"}
# The diagrams are repo-authored, but a CSP still stops any script in one
# from running if the file is opened directly rather than through <img>.
_SVG_HEADERS = {
    "Cache-Control": "public, max-age=86400",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
}

router = APIRouter(prefix="/glossary", tags=["glossary"])


@lru_cache(maxsize=1)
def _document() -> Tuple[bytes, str]:
    """Read the glossary once and return its bytes and a strong ETag.

    Parsing here makes a malformed file fail on the first request rather
    than reach the browser.
    """
    raw = GLOSSARY_PATH.read_bytes()
    json.loads(raw)
    return raw, '"' + hashlib.sha256(raw).hexdigest() + '"'


def load_glossary() -> Dict[str, Any]:
    """Return the glossary as a dict (for tests and future server-side use)."""
    return json.loads(_document()[0])


def _etag_matches(header: str, etag: str) -> bool:
    """True when an ``If-None-Match`` header names ``etag`` (or is ``*``)."""
    candidates = [part.strip() for part in header.split(",")]
    return "*" in candidates or etag in candidates


@router.get("")
def glossary(request: Request) -> Response:
    """Serve the whole glossary, or 304 when the client's copy is current."""
    raw, etag = _document()
    headers = {"ETag": etag, **_CACHE_HEADERS}
    if _etag_matches(request.headers.get("if-none-match", ""), etag):
        return Response(status_code=304, headers=headers)
    return Response(content=raw, media_type="application/json", headers=headers)


@router.get("/img/{name}")
def image(name: str) -> FileResponse:
    """Serve one diagram by file name; anything outside the pattern is 404."""
    path = IMAGE_DIR / name
    if not _IMAGE_NAME.fullmatch(name) or not path.is_file():
        raise HTTPException(status_code=404, detail="No such diagram")
    return FileResponse(path, media_type="image/svg+xml", headers=_SVG_HEADERS)
