"""
chatbot/providers.py
====================
Which OpenAI-compatible chat endpoint the assistant talks to.

The agent speaks the OpenAI Chat Completions format, which OpenRouter,
DeepSeek, OpenAI, Groq, Together, Ollama, vLLM and most other hosts accept,
so a provider is only a base URL, the env var holding its key and a default
model. Selection, all from the environment:

    SS_LLM_PROVIDER   openrouter | deepseek | custom. Unset: openrouter when
                      OPENROUTER_API_KEY is set, else deepseek when
                      DEEPSEEK_API_KEY is set, else openrouter (and the key
                      error names both).
    SS_LLM_MODEL      overrides the preset's model; required for custom.
    SS_LLM_BASE_URL   overrides the preset's URL; required for custom.
    SS_LLM_API_KEY    the key for custom.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, replace
from typing import Dict, Mapping, Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)

PROVIDER_ENV = "SS_LLM_PROVIDER"
MODEL_ENV = "SS_LLM_MODEL"
BASE_URL_ENV = "SS_LLM_BASE_URL"
CUSTOM_KEY_ENV = "SS_LLM_API_KEY"
CUSTOM = "custom"


@dataclass(frozen=True)
class Provider:
    """One OpenAI-compatible endpoint: where it is, its key's env var, its default model."""

    #: Name as given in SS_LLM_PROVIDER.
    name: str
    #: Base URL the OpenAI client appends /chat/completions to.
    base_url: str
    #: Env var that holds this provider's API key.
    key_env: str
    #: Model used when neither the caller nor SS_LLM_MODEL names one.
    default_model: Optional[str]
    #: Headers sent with every request (OpenRouter's app attribution).
    extra_headers: Mapping[str, str] = field(default_factory=dict)


#: Presets, in auto-pick order: the first whose key is set wins.
PROVIDERS: Dict[str, Provider] = {
    "openrouter": Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        key_env="OPENROUTER_API_KEY",
        default_model="deepseek/deepseek-v4-flash",
        extra_headers={"X-Title": "Surya Siddhanta"},
    ),
    "deepseek": Provider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-v4-flash",
    ),
}

DEFAULT_PROVIDER = "openrouter"

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class LLMSettings:
    """Everything the agent needs to build its client, resolved once."""

    #: Provider name, for traces and error messages.
    provider: str
    #: Base URL of the chat endpoint.
    base_url: str
    #: The API key; kept out of repr so it never lands in a log line.
    api_key: str = field(repr=False)
    #: Model name sent with every request.
    model: str
    #: Extra headers for every request.
    headers: Mapping[str, str] = field(default_factory=dict)


def _valid_names() -> str:
    """The accepted SS_LLM_PROVIDER values, for error messages."""
    return ", ".join([*PROVIDERS, CUSTOM])


def resolve_provider(name: Optional[str] = None,
                     environ: Optional[Mapping[str, str]] = None) -> Provider:
    """
    The provider to use: `name`, else SS_LLM_PROVIDER, else the first preset whose key is set.

    With nothing named and no key set this returns the default (OpenRouter),
    so the caller's key check reports what to set. SS_LLM_BASE_URL replaces
    a preset's URL.

    Raises:
        ValueError: for an unknown name, or `custom` without SS_LLM_BASE_URL,
            SS_LLM_API_KEY and SS_LLM_MODEL.
    """
    env = os.environ if environ is None else environ
    chosen = (name or env.get(PROVIDER_ENV) or "").strip().lower()
    if not chosen:
        chosen = next((p.name for p in PROVIDERS.values() if env.get(p.key_env)), DEFAULT_PROVIDER)

    if chosen == CUSTOM:
        missing = [v for v in (BASE_URL_ENV, CUSTOM_KEY_ENV, MODEL_ENV) if not env.get(v)]
        if missing:
            raise ValueError(f"{PROVIDER_ENV}=custom needs {', '.join(missing)}")
        return Provider(name=CUSTOM, base_url=env[BASE_URL_ENV],
                        key_env=CUSTOM_KEY_ENV, default_model=env[MODEL_ENV])

    preset = PROVIDERS.get(chosen)
    if preset is None:
        raise ValueError(f"Unknown {PROVIDER_ENV} {chosen!r}; use one of {_valid_names()}")
    override = env.get(BASE_URL_ENV)
    return replace(preset, base_url=override) if override else preset


def resolve_settings(provider: Optional[str] = None,
                     api_key: Optional[str] = None,
                     model: Optional[str] = None,
                     base_url: Optional[str] = None,
                     environ: Optional[Mapping[str, str]] = None) -> LLMSettings:
    """
    Resolve provider, key, model and URL; explicit arguments beat the environment.

    Raises:
        ValueError: when no key is found (the API turns this into a 503),
            when no model is known, or from resolve_provider.
    """
    env = os.environ if environ is None else environ
    chosen = resolve_provider(provider, env)
    key = api_key or env.get(chosen.key_env)
    if not key:
        if provider or env.get(PROVIDER_ENV):
            raise ValueError(f"{chosen.key_env} is not set ({PROVIDER_ENV}={chosen.name})")
        raise ValueError(
            f"{PROVIDERS['openrouter'].key_env} or {PROVIDERS['deepseek'].key_env} is not set "
            f"(or choose a provider with {PROVIDER_ENV}: {_valid_names()})"
        )
    name = model or env.get(MODEL_ENV) or chosen.default_model
    if not name:
        raise ValueError(f"No model for provider {chosen.name}; set {MODEL_ENV}")
    url = base_url or chosen.base_url
    _warn_if_plaintext(url)
    return LLMSettings(provider=chosen.name, base_url=url, api_key=key,
                       model=name, headers=dict(chosen.extra_headers))


def _warn_if_plaintext(url: str) -> None:
    """Warn when the key would travel unencrypted to a host other than this machine."""
    parsed = urlparse(url)
    if parsed.scheme == "http" and parsed.hostname not in _LOCAL_HOSTS:
        log.warning("Chat endpoint %s is plain http; the API key is sent unencrypted", url)
