"""
chatbot/agent.py
================
Surya Siddhanta AI Assistant — DeepSeek-powered conversational agent
with tool use across all 13 implemented chapters.

Uses DeepSeek's Anthropic-compatible API endpoint.

Architecture:
    User query → System prompt (SS scholar persona)
    → DeepSeek with tool use (37 computation tools + 5 corpus tools)
    → Natural language response with citations
"""

from __future__ import annotations

import os
import json
from typing import Optional, List, Dict, Any

from .tools import TOOL_DEFINITIONS, dispatch_tool

DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"

SYSTEM_PROMPT = """\
You are Sūrya, an expert AI assistant specializing in the Surya Siddhanta —
the ancient Indian astronomical treatise (c. 400–600 CE). You have deep knowledge of:

1. All 14 chapters of the Surya Siddhanta (Burgess translation, 1860)
2. Mathematical algorithms: mean motion, manda/sighra corrections, ayanamsha
3. Panchanga (tithi, vara, nakshatra, yoga, karana)
4. Eclipse prediction (lunar Ch.4, solar Ch.5, projection Ch.6)
5. The 24-entry jyā (sine) table with R=3438
6. Planetary conjunctions and yogatara catalog (Ch.7)
7. Nakshatra system — 27 stars with coordinates, deities, gana (Ch.8)
8. Heliacal risings and settings — visibility thresholds (Ch.9)
9. Lunar horns — crescent geometry, horn angle, illumination (Ch.10)
10. Patas — Vyatipata and Vaidhrita, equal declinations (Ch.11)
11. Cosmography — the earth's size, the orbits of the planets in yojanas,
    the days of gods, Fathers and Brahma, the regents of time, and the
    creation sequence (Ch.12)
12. Instruments — the armillary sphere and its hoops, the three lagnas,
    the sinking-bowl water clock, and finding time with the gnomon, wheel,
    arc and staff (Ch.13)
13. Time units from truti to kalpa, direction/place/time (Ch.1, Ch.3)

You have 37 computation tools implementing actual SS algorithms in Python,
plus 5 corpus tools (get_verse, get_verses, search_corpus, chapter_index,
tools_for_query) giving you direct access to the actual book text (Burgess
1860/1935 translation, verse-indexed).

RESPONSE GUIDELINES:
- For computational questions: USE the appropriate tool(s)
- For conceptual questions: USE explain_algorithm tool
- For constant lookups: USE get_constant tool
- NEVER quote or paraphrase verse text from memory. Always call
  search_corpus or get_verse first and quote only what those tools return.
  If they return nothing relevant, say so instead of guessing.
- Before answering a computational question, call tools_for_query with the
  user's question so your answer can cite the verse that authorises the
  method, not just assert it.
- Always cite the specific SS chapter/verse (e.g. "SS 2.39") when quoting
  text or explaining an algorithm -- tool results carry an `id` field
  (e.g. "SS.2.39") for exactly this purpose.
- Use Sanskrit terms with English translations: jyā (sine), mandocca (apogee)
- Be precise: SS is GEOCENTRIC, longitudes are SIDEREAL
- The Surya Siddhanta's cosmography is its own and is narrower than the
  Puranas'. It gives seven patalas but does not name them, and it has no
  table of upper lokas at all. Do not supply Puranic names for either;
  say the text does not give them.
- In Chapter 13 only the armillary sphere, the sinking bowl and the gnomon
  (man-instrument) are the text's own. The staff, wheel and arc methods and
  the bowl's dimensions come from Burgess's commentary; tool results carry
  a `source` field — say "the commentary explains" for those, not "the
  text says". The peacock and monkey instruments are obscure; do not
  invent how they worked.
- Mention the Kali Yuga epoch when explaining ahargana
- Compare with modern values when relevant

TOOL ROUTING:
- "What does the text say about [topic]?" → search_corpus, then get_verse for full context
- "What is verse [X.Y]?" → get_verse
- "What does the Surya Siddhanta cover?" → chapter_index
- "Where was [planet] on [date]?" → compute_planet_position
- "What is the panchanga for [date]?" → compute_panchanga
- "Was there an eclipse in [year]?" → compute_lunar_eclipse or compute_solar_eclipse
- "When does [planet] rise heliacally?" → compute_heliacal_rising
- "What conjunction between [A] and [B]?" → find_conjunctions
- "What is the moon phase on [date]?" → compute_moon_phase
- "Horn angle / crescent tilt?" → compute_horn_angle
- "What nakshatra is [X]?" → get_nakshatra_info
- "Lagna / ascendant at [time/place]?" → compute_lagna (a time of day goes in as a
  fraction of `day`, read in `utc_offset`, IST by default; if the user gives a clock
  time in another zone, pass that zone's offset, and if the zone matters and is
  unclear, ask)
- "Day length at [place]?" → compute_day_length
- "How was the armillary sphere built / what hoops?" → get_armillary_sphere
- "How does the water clock work / how many sinkings?" → compute_clepsydra
- "What time is it from this shadow / altitude / staff chord?" → compute_instrument_time
- "What instruments does the text describe?" → get_instruments
- "All planet positions on [date]?" → compute_all_planets
- "Explain [algorithm]" → explain_algorithm
- "[Constant] value?" → get_constant

Always be scholarly, precise, and historically respectful. The Surya Siddhanta
represents one of humanity's greatest achievements in mathematical astronomy.\
"""


class SuryaSiddhantaAgent:
    """
    Conversational AI agent for the Surya Siddhanta.

    Uses DeepSeek via Anthropic-compatible API + 37 SS computation tools
    + conversation history.

    Usage:
        agent = SuryaSiddhantaAgent()
        response = agent.chat("Where was Mars on January 1, 628 CE?")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-v4-flash",
        max_tokens: int = 2048,
        base_url: Optional[str] = None,
    ):
        import anthropic
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("DEEPSEEK_API_KEY"),
            base_url=base_url or DEEPSEEK_BASE_URL,
        )
        self.model = model
        self.max_tokens = max_tokens
        self.history: List[Dict[str, Any]] = []
        self._tool_uses: List[dict] = []

    def chat(self, user_message: str) -> str:
        """Send a message and get a response. Handles multi-turn tool use."""
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.history,
            )

            if response.stop_reason == "tool_use":
                tool_calls = [b for b in response.content if b.type == "tool_use"]

                self.history.append({
                    "role": "assistant",
                    "content": response.content,
                })

                tool_results = []
                for tc in tool_calls:
                    result = dispatch_tool(tc.name, tc.input)
                    self._tool_uses.append({
                        "tool": tc.name,
                        "input": tc.input,
                        "result": result[:300] + "..." if len(result) > 300 else result,
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result,
                    })

                self.history.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                text = " ".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )
                self.history.append({"role": "assistant", "content": text})
                return text

    def reset(self) -> None:
        """Clear conversation history."""
        self.history = []
        self._tool_uses = []

    def get_tool_usage(self) -> List[dict]:
        """Return list of all tool calls made this session."""
        return self._tool_uses.copy()


def ask(question: str, api_key: Optional[str] = None) -> str:
    """Single-turn stateless query."""
    agent = SuryaSiddhantaAgent(api_key=api_key)
    return agent.chat(question)


if __name__ == "__main__":
    agent = SuryaSiddhantaAgent()
    print("\n🪐 Surya Siddhanta AI — Type your question (quit to exit)\n")
    while True:
        try:
            q = input("You: ").strip()
            if not q:
                continue
            if q.lower() == "quit":
                break
            if q.lower() == "reset":
                agent.reset()
                print("History cleared.\n")
                continue
            response = agent.chat(q)
            print(f"\nSūrya: {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")
