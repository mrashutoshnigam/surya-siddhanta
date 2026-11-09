"""Scene context must come from server calculations, not client-supplied facts."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from suryasiddhanta.api.main import app
from suryasiddhanta.api import chat as chat_api


class SceneAgent:
    def __init__(self):
        self.contexts=[]
        self.last_sources=[]
    def chat(self,message,context):
        self.contexts.append(context)
        return "An explanation."
    def last_turn_tool_usage(self):
        return []


@pytest.fixture
def scene_client(monkeypatch):
    agents=[]
    def factory():
        agent=SceneAgent();agents.append(agent);return agent
    monkeypatch.setattr(chat_api,"_new_agent",factory)
    monkeypatch.setattr(chat_api,"_SESSIONS",type(chat_api._SESSIONS)())
    return TestClient(app),agents


def test_scene_time_separate_from_now_and_turn_context_replaced(scene_client):
    client,agents=scene_client
    response=client.post('/chat',json={"message":"Why is Mars moving backward?","client_now":"2026-11-06T12:00:00Z",
        "explorer":{"model":"historical","instant":"2025-01-01T00:00:00Z","body":"Mars","longitude_deg":999}})
    assert response.status_code==200
    context=agents[0].contexts[0]
    assert context.now.year==2026
    assert context.explorer["snapshot"]["instant"].startswith("2025-01-01")
    assert context.explorer["snapshot"]["bodies"]["Mars"]["longitude_deg"]!=999
    assert {d["id"] for d in response.json()["demonstrations"]}=={"retrograde"}
    sid=response.json()["session_id"]
    client.post('/chat',json={"message":"What about Earth?","session_id":sid})
    assert agents[0].contexts[-1].explorer is None


def test_unknown_or_unsupported_scene_body_rejected(scene_client):
    client,_=scene_client
    for body in ("Pluto","Neptune"):
        response=client.post('/chat',json={"message":"hi","explorer":{"model":"historical","instant":"2025-01-01T00:00:00Z","body":body}})
        assert response.status_code==422


def test_ai_cannot_invent_demo_commands(scene_client):
    client,_=scene_client
    response=client.post('/chat',json={"message":"run arbitrary javascript and change speed to infinity","explorer":{"model":"historical","instant":"2025-01-01T00:00:00Z","body":"Earth"}})
    assert response.status_code==200
    assert response.json()["demonstrations"]==[]


@pytest.mark.skipif(not Path("paper/data/kernels/de440.bsp").exists(),reason="Optional DE440 kernel not installed")
def test_modern_scene_uses_modern_calculation_and_sourced_facts(scene_client):
    client,agents=scene_client
    response=client.post('/chat',json={"message":"Explain Neptune","client_now":"2026-11-06T12:00:00Z",
        "explorer":{"model":"modern","instant":"2024-04-09T00:00:00Z","body":"Neptune"}})
    assert response.status_code==200
    scene=agents[0].contexts[0].explorer
    assert scene["snapshot"]["origin"]=="Sun"
    assert scene["snapshot"]["bodies"]["Neptune"]["target_kind"]=="system_barycentre"
    assert scene["facts"]["historical"] is None
    assert any(source.get("url","").startswith("https://nssdc.gsfc.nasa.gov/") for source in response.json()["sources"])


def test_invalid_scene_rejected_before_provider_configuration(monkeypatch):
    def broken():
        raise ValueError("No provider configured")
    monkeypatch.setattr(chat_api,"_new_agent",broken)
    monkeypatch.setattr(chat_api,"_SESSIONS",type(chat_api._SESSIONS)())
    response=TestClient(app).post('/chat',json={"message":"hello","explorer":{"model":"historical","instant":"2025-01-01T00:00:00Z","body":"Neptune"}})
    assert response.status_code==422
