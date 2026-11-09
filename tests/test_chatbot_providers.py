"""Tests for chat provider selection (chatbot/providers.py) and the agent's client wiring.

Resolution is tested against explicit `environ` dicts so the developer's own
keys never leak into a result; the agent tests clear the relevant env vars
with monkeypatch and inspect the OpenAI client it builds, with no network.
"""
import logging

import pytest

from suryasiddhanta.chatbot.providers import (
    PROVIDERS, resolve_provider, resolve_settings)

PROVIDER_VARS = ("SS_LLM_PROVIDER", "SS_LLM_MODEL", "SS_LLM_BASE_URL", "SS_LLM_API_KEY",
                 "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY")


# ── resolve_provider ────────────────────────────────────────────

def test_auto_pick_prefers_openrouter_when_both_keys_are_set():
    """
    With no provider named and both keys present, OpenRouter (the default)
    wins.
    Expected: provider "openrouter".
    """
    env = {"OPENROUTER_API_KEY": "or", "DEEPSEEK_API_KEY": "ds"}
    assert resolve_provider(environ=env).name == "openrouter"


def test_auto_pick_falls_back_to_deepseek_key():
    """
    A deploy that only has DEEPSEEK_API_KEY keeps working without naming a
    provider.
    Expected: provider "deepseek".
    """
    assert resolve_provider(environ={"DEEPSEEK_API_KEY": "ds"}).name == "deepseek"


def test_no_name_and_no_key_resolves_to_the_default():
    """
    With nothing configured, the default provider comes back so the key
    check can report what to set.
    Expected: provider "openrouter".
    """
    assert resolve_provider(environ={}).name == "openrouter"


def test_env_var_names_the_provider_case_insensitively():
    """
    SS_LLM_PROVIDER overrides the key-based pick and ignores case and
    surrounding space.
    Expected: " DeepSeek " selects deepseek even with an OpenRouter key set.
    """
    env = {"SS_LLM_PROVIDER": " DeepSeek ", "OPENROUTER_API_KEY": "or"}
    assert resolve_provider(environ=env).name == "deepseek"


def test_explicit_name_beats_the_env_var():
    """
    A name passed by the caller wins over SS_LLM_PROVIDER.
    Expected: provider "openrouter".
    """
    assert resolve_provider("openrouter", {"SS_LLM_PROVIDER": "deepseek"}).name == "openrouter"


def test_unknown_provider_lists_the_valid_names():
    """
    A typo in SS_LLM_PROVIDER fails loudly rather than silently picking one.
    Expected: ValueError naming every valid provider.
    """
    with pytest.raises(ValueError, match="openrouter, deepseek, custom"):
        resolve_provider(environ={"SS_LLM_PROVIDER": "openrouterr"})


def test_base_url_env_overrides_a_preset_url():
    """
    SS_LLM_BASE_URL replaces a preset's URL but keeps its key var and model.
    Expected: deepseek preset with the mirror URL.
    """
    env = {"SS_LLM_PROVIDER": "deepseek", "SS_LLM_BASE_URL": "https://mirror.example/v1"}
    provider = resolve_provider(environ=env)
    assert provider.base_url == "https://mirror.example/v1"
    assert provider.key_env == "DEEPSEEK_API_KEY"
    assert provider.default_model == PROVIDERS["deepseek"].default_model


def test_custom_provider_needs_url_key_and_model():
    """
    The custom endpoint has no defaults, so every missing setting is named.
    Expected: ValueError listing all three env vars.
    """
    with pytest.raises(ValueError, match="SS_LLM_BASE_URL, SS_LLM_API_KEY, SS_LLM_MODEL"):
        resolve_provider(environ={"SS_LLM_PROVIDER": "custom"})


def test_custom_provider_is_built_from_the_env():
    """
    A fully configured custom endpoint (e.g. a local Ollama) resolves to its
    URL, key and model.
    Expected: settings carry the env values and no extra headers.
    """
    env = {"SS_LLM_PROVIDER": "custom", "SS_LLM_BASE_URL": "http://localhost:11434/v1",
           "SS_LLM_API_KEY": "ollama", "SS_LLM_MODEL": "qwen3"}
    settings = resolve_settings(environ=env)
    assert (settings.provider, settings.base_url, settings.api_key, settings.model) == (
        "custom", "http://localhost:11434/v1", "ollama", "qwen3")
    assert settings.headers == {}


# ── resolve_settings ────────────────────────────────────────────

def test_missing_key_after_auto_pick_names_both_keys():
    """
    With nothing configured, the error tells the user both ways to fix it.
    Expected: ValueError naming OPENROUTER_API_KEY and DEEPSEEK_API_KEY.
    """
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY or DEEPSEEK_API_KEY"):
        resolve_settings(environ={})


def test_missing_key_for_a_named_provider_names_only_its_key():
    """
    When the provider was chosen explicitly, the error names just its key.
    Expected: ValueError naming DEEPSEEK_API_KEY and the chosen provider.
    """
    with pytest.raises(ValueError, match=r"DEEPSEEK_API_KEY is not set \(SS_LLM_PROVIDER=deepseek\)"):
        resolve_settings(environ={"SS_LLM_PROVIDER": "deepseek", "OPENROUTER_API_KEY": "or"})


def test_model_precedence_is_argument_then_env_then_default():
    """
    An explicit model beats SS_LLM_MODEL, which beats the preset default.
    Expected: each layer wins in turn.
    """
    env = {"OPENROUTER_API_KEY": "or"}
    assert resolve_settings(environ=env).model == "deepseek/deepseek-v4-flash"
    env["SS_LLM_MODEL"] = "anthropic/claude-sonnet-5.5"
    assert resolve_settings(environ=env).model == "anthropic/claude-sonnet-5.5"
    assert resolve_settings(model="x/y", environ=env).model == "x/y"


def test_api_key_never_appears_in_repr():
    """
    Settings may be logged while debugging; the key must not be in its repr.
    Expected: the key string is absent from repr().
    """
    settings = resolve_settings(environ={"OPENROUTER_API_KEY": "sk-or-secret"})
    assert "sk-or-secret" not in repr(settings)


def test_plain_http_to_a_remote_host_warns(caplog):
    """
    A non-local http:// endpoint would send the key in clear text, so a
    warning is logged; localhost is exempt.
    Expected: one warning for the remote URL, none for localhost.
    """
    base = {"SS_LLM_PROVIDER": "custom", "SS_LLM_API_KEY": "k", "SS_LLM_MODEL": "m"}
    with caplog.at_level(logging.WARNING, logger="suryasiddhanta.chatbot.providers"):
        resolve_settings(environ={**base, "SS_LLM_BASE_URL": "http://localhost:8000/v1"})
        assert not caplog.records
        resolve_settings(environ={**base, "SS_LLM_BASE_URL": "http://llm.example.com/v1"})
    assert len(caplog.records) == 1 and "unencrypted" in caplog.records[0].getMessage()


# ── Agent wiring ────────────────────────────────────────────────

@pytest.fixture
def clean_env(monkeypatch):
    """Clear every provider env var so the developer's own config cannot leak in."""
    for var in PROVIDER_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def test_agent_defaults_to_openrouter_with_attribution_header(clean_env):
    """
    With only an OpenRouter key, the agent's client targets OpenRouter with
    the preset model and the X-Title attribution header.
    Expected: base URL, model, provider and header as the preset says.
    """
    pytest.importorskip("openai")
    from suryasiddhanta.chatbot.agent import SuryaSiddhantaAgent
    clean_env.setenv("OPENROUTER_API_KEY", "sk-or-test")
    agent = SuryaSiddhantaAgent()
    assert agent.provider == "openrouter"
    assert agent.model == "deepseek/deepseek-v4-flash"
    assert str(agent.client.base_url).rstrip("/") == "https://openrouter.ai/api/v1"
    assert agent.client.api_key == "sk-or-test"
    assert agent.client.default_headers["X-Title"] == "Surya Siddhanta"


def test_agent_uses_deepseek_when_selected(clean_env):
    """
    SS_LLM_PROVIDER=deepseek points the client at DeepSeek's OpenAI-format
    endpoint with its own key and no OpenRouter header.
    Expected: DeepSeek URL, key and model; no X-Title header.
    """
    pytest.importorskip("openai")
    from suryasiddhanta.chatbot.agent import SuryaSiddhantaAgent
    clean_env.setenv("SS_LLM_PROVIDER", "deepseek")
    clean_env.setenv("DEEPSEEK_API_KEY", "sk-ds-test")
    agent = SuryaSiddhantaAgent()
    assert agent.provider == "deepseek"
    assert agent.model == "deepseek-v4-flash"
    assert str(agent.client.base_url).rstrip("/") == "https://api.deepseek.com"
    assert agent.client.api_key == "sk-ds-test"
    assert "X-Title" not in agent.client.default_headers


def test_agent_arguments_override_the_environment(clean_env):
    """
    Constructor arguments (provider, key, model, URL) win over env settings.
    Expected: the client reflects the arguments, not the env.
    """
    pytest.importorskip("openai")
    from suryasiddhanta.chatbot.agent import SuryaSiddhantaAgent
    clean_env.setenv("OPENROUTER_API_KEY", "sk-or-env")
    clean_env.setenv("SS_LLM_MODEL", "env/model")
    agent = SuryaSiddhantaAgent(provider="deepseek", api_key="arg-key", model="arg-model",
                                base_url="https://proxy.example/v1")
    assert agent.provider == "deepseek"
    assert agent.model == "arg-model"
    assert agent.client.api_key == "arg-key"
    assert str(agent.client.base_url).rstrip("/") == "https://proxy.example/v1"
