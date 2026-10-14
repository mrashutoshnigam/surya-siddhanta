"""Thin REST wrappers around suryasiddhanta.corpus.retrieve, for a standalone
verse-browser panel in the UI. Not required for the chatbot itself -- the
LLM calls retrieve.py's functions directly as tools (see chatbot/tools.py).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.get("/chapters")
def chapters() -> Dict[str, Any]:
    from suryasiddhanta.corpus.retrieve import chapter_index
    return {"chapters": chapter_index()}


@router.get("/verse/{chapter}/{verse}")
def verse(chapter: int, verse: int) -> Dict[str, Any]:
    from suryasiddhanta.corpus.retrieve import get_verse
    result = get_verse(chapter, verse)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No verse found at {chapter}.{verse}")
    return result


@router.get("/verses/{chapter}")
def verses(chapter: int, start: Optional[int] = None, end: Optional[int] = None) -> Dict[str, Any]:
    from suryasiddhanta.corpus.retrieve import get_verses
    return {"verses": get_verses(chapter, start, end)}


@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 8) -> Dict[str, Any]:
    from suryasiddhanta.corpus.retrieve import search as _search
    return {"results": _search(q, limit)}
