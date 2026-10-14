"""Chat endpoint wrapping SuryaSiddhantaAgent, one agent per browser session.

In-memory session store -- fine for the local single-user dev target this
project is scoped to. Restarting the API drops all sessions.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from suryasiddhanta.chatbot.agent import SuryaSiddhantaAgent

from .schemas import ChatIn

router = APIRouter(prefix="/chat", tags=["chat"])

_SESSIONS: Dict[str, SuryaSiddhantaAgent] = {}


@router.post("")
def chat(body: ChatIn) -> Dict[str, Any]:
    session_id = body.session_id or str(uuid.uuid4())
    agent = _SESSIONS.get(session_id)
    if agent is None:
        agent = SuryaSiddhantaAgent()
        _SESSIONS[session_id] = agent

    try:
        reply = agent.chat(body.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "session_id": session_id,
        "reply": reply,
        "tool_uses": agent.get_tool_usage(),
    }


@router.post("/{session_id}/reset")
def reset(session_id: str) -> Dict[str, Any]:
    agent = _SESSIONS.get(session_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    agent.reset()
    return {"session_id": session_id, "status": "reset"}
