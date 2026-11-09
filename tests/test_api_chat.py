"""Tests for the /chat endpoint (api/chat.py) with a stubbed agent.

The real agent needs a DeepSeek key and the network, so `_new_agent` is
replaced by a stub that records what it is asked and replies at once.
"""
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from suryasiddhanta.api import chat as chat_api  # noqa: E402
from suryasiddhanta.api.main import app  # noqa: E402


class StubAgent:
    """Minimal stand-in for SuryaSiddhantaAgent."""

    def __init__(self):
        """Start with no recorded turns."""
        self.calls = []
        self.reset_count = 0
        self.last_sources = [{"id": "SS.2.39", "kind": "verse"}]

    def chat(self, message, context=None):
        """Record the turn and echo the message."""
        self.calls.append((message, context))
        return f"echo: {message}"

    def last_turn_tool_usage(self):
        """One fake tool call per turn."""
        return [{"tool": "get_constant", "input": {}, "result": "{}"}]

    def reset(self):
        """Count resets."""
        self.reset_count += 1


@pytest.fixture
def client(monkeypatch):
    """A TestClient whose sessions get StubAgents, with a clean session store."""
    agents = []

    def factory():
        agent = StubAgent()
        agents.append(agent)
        return agent

    monkeypatch.setattr(chat_api, "_new_agent", factory)
    monkeypatch.setattr(chat_api, "_SESSIONS", type(chat_api._SESSIONS)())
    test_client = TestClient(app)
    test_client.agents = agents
    return test_client


def test_chat_returns_reply_session_and_turn_tools(client):
    """
    A first message creates a session and returns this turn's tool calls.
    Expected: echoed reply, a session id, one tool use.
    """
    r = client.post("/chat", json={"message": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["reply"] == "echo: hello"
    assert body["session_id"]
    assert len(body["tool_uses"]) == 1
    assert body["sources"] == [{"id": "SS.2.39", "kind": "verse"}]


def test_session_is_reused(client):
    """
    Passing the returned session id continues the same agent.
    Expected: one agent created, two turns recorded on it.
    """
    sid = client.post("/chat", json={"message": "a"}).json()["session_id"]
    client.post("/chat", json={"message": "b", "session_id": sid})
    assert len(client.agents) == 1
    assert [m for m, _ in client.agents[0].calls] == ["a", "b"]


def test_context_fields_reach_the_agent(client):
    """
    The client's moment and place become the turn's ChatContext.
    Expected: the agent sees Delhi's coordinates and the client's hour.
    """
    client.post("/chat", json={
        "message": "Jupiter now?", "client_now": "2026-10-18T18:00:00+05:30",
        "place": "Delhi", "latitude": 28.61, "longitude": 77.21,
    })
    _, ctx = client.agents[0].calls[0]
    assert (ctx.place, ctx.latitude, ctx.longitude) == ("Delhi", 28.61, 77.21)
    assert ctx.now.hour == 18 and ctx.utc_offset == 5.5


def test_out_of_range_coordinates_are_rejected(client):
    """
    Coordinates are validated before reaching the agent.
    Expected: 422 for latitude 95.
    """
    r = client.post("/chat", json={"message": "x", "latitude": 95, "longitude": 0})
    assert r.status_code == 422


def test_missing_key_gives_503(monkeypatch):
    """
    When the agent cannot be built for lack of a key, the client gets a
    clear 503, not a 500.
    Expected: 503 whose detail mentions the configuration.
    """
    def broken():
        raise ValueError("DEEPSEEK_API_KEY is not set")

    monkeypatch.setattr(chat_api, "_new_agent", broken)
    monkeypatch.setattr(chat_api, "_SESSIONS", type(chat_api._SESSIONS)())
    r = TestClient(app).post("/chat", json={"message": "hi"})
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"]


def test_session_store_is_capped(client, monkeypatch):
    """
    The in-memory store drops the least recently used sessions.
    Expected: no more than MAX_SESSIONS sessions after many new ones.
    """
    monkeypatch.setattr(chat_api, "MAX_SESSIONS", 3)
    for _ in range(5):
        client.post("/chat", json={"message": "x"})
    assert len(chat_api._SESSIONS) == 3


def test_reset_clears_known_session_and_404s_unknown(client):
    """
    Reset reaches the session's agent; an unknown id is a 404.
    Expected: reset_count 1 for the known session, 404 otherwise.
    """
    sid = client.post("/chat", json={"message": "a"}).json()["session_id"]
    assert client.post(f"/chat/{sid}/reset").status_code == 200
    assert client.agents[0].reset_count == 1
    assert client.post("/chat/nope/reset").status_code == 404
