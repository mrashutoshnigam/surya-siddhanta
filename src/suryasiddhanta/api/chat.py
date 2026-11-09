"""Chat endpoint wrapping SuryaSiddhantaAgent, one agent per browser session.

In-memory session store -- fine for the local single-user dev target this
project is scoped to. Restarting the API drops all sessions. The store is
capped (least recently used sessions are dropped) and each session has a
lock, because two requests on one session would interleave its history.
"""
from __future__ import annotations

import logging
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field, replace
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from suryasiddhanta.chatbot.agent import ChatContext, SuryaSiddhantaAgent

from .schemas import ChatIn

router = APIRouter(prefix="/chat", tags=["chat"])
log = logging.getLogger(__name__)

#: Sessions kept in memory; the least recently used is dropped beyond this.
MAX_SESSIONS = 100


@dataclass
class _Session:
    """One browser session's agent and the lock serialising its turns."""

    agent: SuryaSiddhantaAgent
    lock: threading.Lock = field(default_factory=threading.Lock)


_SESSIONS: "OrderedDict[str, _Session]" = OrderedDict()
_STORE_LOCK = threading.Lock()


def _new_agent() -> SuryaSiddhantaAgent:
    """Build an agent; a seam the tests replace with a scripted one."""
    return SuryaSiddhantaAgent()


def _session(session_id: str) -> _Session:
    """
    The session for an id, created on first use, marked most recently used.

    Raises:
        HTTPException 503: when the chat provider is not configured.
    """
    with _STORE_LOCK:
        session = _SESSIONS.get(session_id)
        if session is None:
            try:
                session = _Session(_new_agent())
            except ValueError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Chat is not configured: {e}. Set it and restart the API.",
                ) from e
            _SESSIONS[session_id] = session
            while len(_SESSIONS) > MAX_SESSIONS:
                _SESSIONS.popitem(last=False)
        _SESSIONS.move_to_end(session_id)
        return session


@router.post("")
def chat(body: ChatIn) -> Dict[str, Any]:
    """
    One chat turn: the reply, this turn's tool calls and the cited sources.

    The request may carry the user's moment and place (see ChatIn); the
    agent resolves relative dates and default places from them.
    """
    session_id = body.session_id or str(uuid.uuid4())
    context = ChatContext.create(
        client_now=body.client_now, utc_offset=body.utc_offset,
        place=body.place, latitude=body.latitude, longitude=body.longitude,
    )
    scene = None
    if body.explorer is not None:
        from .explorer_chat import scene_context
        from .explorer_core import EphemerisUnavailable
        try:
            scene = scene_context(body.explorer)
        except EphemerisUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        context = replace(context, explorer=scene)
    session = _session(session_id)
    if not session.lock.acquire(timeout=120):
        raise HTTPException(status_code=409, detail="This session is still answering")
    try:
        reply = session.agent.chat(body.message, context)
        tool_uses = session.agent.last_turn_tool_usage()
        sources = list(getattr(session.agent, "last_sources", []))
    except Exception as e:
        log.exception("chat turn failed")
        raise HTTPException(status_code=502, detail=f"Chat provider error: {e}") from e
    finally:
        session.lock.release()

    result = {
        "session_id": session_id,
        "reply": reply,
        "tool_uses": tool_uses,
        "sources": sources,
    }
    if scene is not None:
        from .explorer_chat import demonstrations, scene_sources
        result["demonstrations"] = demonstrations(body.message)
        result["sources"] += scene_sources(scene)
    return result


@router.post("/{session_id}/reset")
def reset(session_id: str) -> Dict[str, Any]:
    """Clear one session's history; 404 for an unknown session."""
    with _STORE_LOCK:
        session = _SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    with session.lock:
        session.agent.reset()
    return {"session_id": session_id, "status": "reset"}
