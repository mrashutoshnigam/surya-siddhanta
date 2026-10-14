"""
chatbot — Surya Siddhanta AI Assistant
=======================================
LLM conversational agent with tool-use over all 14 chapters of the
Surya Siddhanta astronomical library.

Components:
  - tools.py  : Tool definitions + dispatch (ch01–ch14)
  - agent.py  : Conversational agent (DeepSeek + agentic tool loop)
"""

from .agent import SuryaSiddhantaAgent, ask

__all__ = ["SuryaSiddhantaAgent", "ask"]
