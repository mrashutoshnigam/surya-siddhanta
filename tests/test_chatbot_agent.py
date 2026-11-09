"""Tests for SuryaSiddhantaAgent's turn handling, with a scripted fake client.

No network: the OpenAI-compatible client is replaced by a stub that
returns pre-written chat completions and records every request, so the
tests can check what the model is sent (system prompt, context block,
retrieved verses, tool results) and how the tool loop behaves.
"""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

pytest.importorskip("openai")

from suryasiddhanta.chatbot.agent import (  # noqa: E402
    OPENAI_TOOLS, SYSTEM_PROMPT, ChatContext, Retrieval, SuryaSiddhantaAgent)
from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS  # noqa: E402


def completion(message, finish_reason):
    """A chat completion with one choice holding `message`."""
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish_reason, message=message)])


def text_response(text, finish_reason="stop"):
    """A model reply that ends the turn with plain text."""
    return completion(SimpleNamespace(content=text, tool_calls=None), finish_reason)


def tool_call(name, args, call_id="call_1"):
    """One function call; `args` is a dict (sent as JSON) or a raw string."""
    arguments = args if isinstance(args, str) else json.dumps(args)
    return SimpleNamespace(id=call_id, type="function",
                           function=SimpleNamespace(name=name, arguments=arguments))


def tool_response(name, args, call_id="call_1", finish_reason="tool_calls", **extra):
    """A model reply that asks for one tool call; `extra` adds message fields."""
    message = SimpleNamespace(content=None, tool_calls=[tool_call(name, args, call_id)], **extra)
    return completion(message, finish_reason)


class FakeClient:
    """Stands in for openai.OpenAI: replays completions, records requests."""

    def __init__(self, responses):
        """Queue the responses to return, in order."""
        self.responses = list(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        """Record the request (with a snapshot of the history) and pop a reply."""
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


def make_agent(responses, retrieval=None):
    """
    An agent wired to a FakeClient with the given scripted responses.

    Pre-retrieval is stubbed (empty unless `retrieval` is given) so loop tests
    do not depend on the corpus; the retrieval tests below use the real one.
    """
    agent = SuryaSiddhantaAgent(api_key="test-key")
    agent.client = FakeClient(responses)
    agent.retrieve = lambda question: retrieval or Retrieval()
    return agent


def first_user_text(request):
    """Text of the first user message in a recorded request (after the system prompt)."""
    return next(m["content"] for m in request["messages"] if m["role"] == "user")


# ── ChatContext ─────────────────────────────────────────────────

def test_context_uses_client_moment_and_offset():
    """
    A client moment with an offset sets both the time and the zone.
    Expected: rendered block shows the client's local date/time and offset.
    """
    ctx = ChatContext.create(client_now="2026-10-18T14:05:00+05:30")
    block = ctx.render()
    assert "2026-10-18 14:05" in block
    assert "utc_offset=5.5" in block
    assert "Ujjain" in block


def test_context_converts_utc_moment_into_given_zone():
    """
    A UTC moment ("Z") with an explicit utc_offset is shown in that zone.
    Expected: 08:35Z reads as 14:05 at UTC+5:30.
    """
    ctx = ChatContext.create(client_now="2026-10-18T08:35:00Z", utc_offset=5.5)
    assert ctx.now.strftime("%H:%M") == "14:05"


def test_context_place_requires_both_coordinates():
    """
    A place is only taken when both latitude and longitude are given.
    Expected: Delhi coordinates are used; a lone latitude falls back to Ujjain.
    """
    delhi = ChatContext.create(place="Delhi", latitude=28.61, longitude=77.21)
    assert (delhi.latitude, delhi.longitude, delhi.place) == (28.61, 77.21, "Delhi")
    partial = ChatContext.create(latitude=10.0)
    assert (partial.latitude, partial.longitude) == (23.18, 75.78)


def test_context_bad_client_time_falls_back_to_server_clock():
    """
    An unparsable client time is ignored rather than failing the turn.
    Expected: the context's moment is within a minute of the server's now.
    """
    ctx = ChatContext.create(client_now="not-a-date", utc_offset=0)
    now = datetime.now(timezone(timedelta(0)))
    assert abs((ctx.now - now).total_seconds()) < 60


# ── Turn handling ───────────────────────────────────────────────

def test_context_block_reaches_the_model():
    """
    Every user turn is sent with the [Context] block before the question, so
    the model can resolve relative dates.
    Expected: the first message starts with [Context] and ends with the question.
    """
    agent = make_agent([text_response("ok")])
    ctx = ChatContext.create(client_now="2026-10-18T14:05:00+05:30")
    agent.chat("What is today's tithi?", ctx)
    sent = first_user_text(agent.client.requests[0])
    assert sent.startswith("[Context]")
    assert "2026-10-18" in sent
    assert sent.endswith("What is today's tithi?")


def test_tool_call_is_dispatched_and_result_returned_to_model():
    """
    A tool call is executed with the model's arguments and the result is
    sent back as a tool message before the final answer.
    Expected: second request carries the assistant's tool_calls turn, then a
    tool message for call_1 holding the panchanga JSON; the final text is
    returned.
    """
    agent = make_agent([
        tool_response("compute_panchanga", {"year": 2026, "month": 10, "day": 18}),
        text_response("Tithi is ..."),
    ])
    reply = agent.chat("Panchanga for 18 Oct 2026?")
    assert reply == "Tithi is ..."
    *_, call_turn, tool_turn = agent.client.requests[1]["messages"]
    assert call_turn["role"] == "assistant"
    assert call_turn["tool_calls"][0]["function"]["name"] == "compute_panchanga"
    assert tool_turn["role"] == "tool" and tool_turn["tool_call_id"] == "call_1"
    assert "tithi" in tool_turn["content"].lower()


def test_system_prompt_is_sent_first_and_not_stored():
    """
    The system prompt leads every request but is not kept in history, so
    history trimming never has to protect it.
    Expected: messages[0] is the system prompt; history has no system turn.
    """
    agent = make_agent([text_response("ok")])
    agent.chat("hello")
    first = agent.client.requests[0]["messages"][0]
    assert first == {"role": "system", "content": SYSTEM_PROMPT}
    assert all(m["role"] != "system" for m in agent.history)


def test_tools_are_sent_as_openai_functions():
    """
    Every TOOL_DEFINITIONS entry is offered as an OpenAI function tool whose
    parameters are the tool's input_schema.
    Expected: one function per definition, names and schemas carried over.
    """
    agent = make_agent([text_response("ok")])
    agent.chat("hello")
    sent = agent.client.requests[0]["tools"]
    assert sent is OPENAI_TOOLS and len(sent) == len(TOOL_DEFINITIONS)
    for tool, definition in zip(sent, TOOL_DEFINITIONS):
        assert tool["type"] == "function"
        assert tool["function"]["name"] == definition["name"]
        assert tool["function"]["parameters"] == definition["input_schema"]


def test_tool_calls_run_even_when_finish_reason_is_stop():
    """
    Some OpenRouter upstreams report finish_reason "stop" alongside tool
    calls; the loop keys on the calls, so they still run.
    Expected: the tool is dispatched and the final text comes from round two.
    """
    agent = make_agent([
        tool_response("get_constant", {"constant_name": "kalpa"}, finish_reason="stop"),
        text_response("done"),
    ])
    assert agent.chat("kalpa?") == "done"
    assert [u["tool"] for u in agent.last_turn_tool_usage()] == ["get_constant"]


def test_malformed_tool_arguments_go_back_to_the_model():
    """
    Arguments that are not a JSON object are answered with an error tool
    message instead of raising, so the model can retry.
    Expected: no exception; the tool message for call_1 carries the error.
    """
    agent = make_agent([tool_response("get_constant", "{not json"), text_response("retry")])
    assert agent.chat("kalpa?") == "retry"
    tool_turn = agent.client.requests[1]["messages"][-1]
    assert tool_turn["role"] == "tool" and tool_turn["tool_call_id"] == "call_1"
    assert "not a JSON object" in tool_turn["content"]


def test_reasoning_content_is_kept_on_the_tool_call_turn():
    """
    DeepSeek's thinking mode needs reasoning_content sent back while a tool
    loop runs, so the assistant turn in history keeps it.
    Expected: the assistant turn in the second request has reasoning_content.
    """
    agent = make_agent([
        tool_response("get_constant", {"constant_name": "kalpa"}, reasoning_content="think"),
        text_response("ok"),
    ])
    agent.chat("kalpa?")
    call_turn = agent.client.requests[1]["messages"][-2]
    assert call_turn["reasoning_content"] == "think"


# ── Loop robustness ─────────────────────────────────────────────

def test_missing_api_key_raises_value_error(monkeypatch):
    """
    With no key given and neither provider key nor SS_LLM_PROVIDER set,
    construction fails with a ValueError the API turns into a 503, not a
    failed request later.
    Expected: ValueError naming both OPENROUTER_API_KEY and DEEPSEEK_API_KEY.
    """
    for var in ("OPENROUTER_API_KEY", "DEEPSEEK_API_KEY", "SS_LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY or DEEPSEEK_API_KEY"):
        SuryaSiddhantaAgent()


def test_tool_round_cap_stops_a_looping_model():
    """
    A host that keeps returning tool calls even when tools are switched off
    is stopped after MAX_TOOL_ROUNDS.
    Expected: exactly MAX_TOOL_ROUNDS requests, a reply saying so, and the
    last round's tool call neither run nor left dangling in the history.
    """
    rounds = SuryaSiddhantaAgent.MAX_TOOL_ROUNDS
    agent = make_agent([tool_response("get_constant", {"constant_name": "kalpa"}, f"c{i}")
                        for i in range(rounds)])
    reply = agent.chat("loop forever")
    assert len(agent.client.requests) == rounds
    assert "tool-call limit" in reply
    called = [m["tool_calls"][0]["id"] for m in agent.history if m.get("tool_calls")]
    assert called == [f"c{i}" for i in range(rounds - 1)]
    assert len(agent.last_turn_tool_usage()) == rounds - 1


def test_last_round_disables_tools_and_takes_the_answer():
    """
    A model that searches until the last round is made to answer from what
    it has gathered: only that final request carries tool_choice="none".
    Expected: earlier requests have no tool_choice, the last one has "none",
    and the text the model gives in that round is the reply.
    """
    rounds = SuryaSiddhantaAgent.MAX_TOOL_ROUNDS
    agent = make_agent([tool_response("get_constant", {"constant_name": "kalpa"}, f"c{i}")
                        for i in range(rounds - 1)] + [text_response("Answer from gathered text.")])
    reply = agent.chat("search a lot")
    assert reply == "Answer from gathered text."
    requests = agent.client.requests
    assert len(requests) == rounds
    assert all("tool_choice" not in r for r in requests[:-1])
    assert requests[-1]["tool_choice"] == "none"
    assert agent.history[-1] == {"role": "assistant", "content": "Answer from gathered text."}


def test_max_tokens_reply_is_flagged_as_cut_off():
    """
    A reply stopped by the token limit is returned with a note, not as if complete.
    Expected: the partial text plus a "cut off" note.
    """
    agent = make_agent([text_response("Partial", finish_reason="length")])
    reply = agent.chat("long question")
    assert reply.startswith("Partial") and "cut off" in reply


def test_tool_trace_is_per_turn():
    """
    last_turn_tool_usage lists only this turn's calls, while get_tool_usage
    keeps the whole session for the older UIs.
    Expected: one call after turn 1, still one (a new one) after turn 2,
    two in the session total.
    """
    agent = make_agent([
        tool_response("get_constant", {"constant_name": "kalpa"}), text_response("a"),
        tool_response("get_constant", {"constant_name": "mahayuga"}), text_response("b"),
    ])
    agent.chat("first")
    assert [u["input"]["constant_name"] for u in agent.last_turn_tool_usage()] == ["kalpa"]
    agent.chat("second")
    assert [u["input"]["constant_name"] for u in agent.last_turn_tool_usage()] == ["mahayuga"]
    assert len(agent.get_tool_usage()) == 2


def test_oversized_tool_result_is_truncated_for_the_model():
    """
    A huge tool result (a whole chapter) is cut before it is sent to the model.
    Expected: the tool message content is at most the cap plus the note.
    """
    agent = make_agent([tool_response("get_verses", {"chapter": 1}), text_response("ok")])
    agent.chat("give me chapter 1")
    content = agent.client.requests[1]["messages"][-1]["content"]
    assert len(content) <= SuryaSiddhantaAgent.MAX_TOOL_RESULT_CHARS + 200


def test_history_is_trimmed_at_turn_boundaries():
    """
    Old turns are dropped whole once MAX_TURNS is reached, and the kept
    history still starts with a plain user turn.
    Expected: at most MAX_TURNS user turns, first message a string user turn.
    """
    agent = make_agent([text_response(str(i)) for i in range(SuryaSiddhantaAgent.MAX_TURNS + 5)])
    for i in range(SuryaSiddhantaAgent.MAX_TURNS + 5):
        agent.chat(f"q{i}")
    users = [m for m in agent.history if m["role"] == "user" and isinstance(m["content"], str)]
    assert len(users) <= SuryaSiddhantaAgent.MAX_TURNS
    assert agent.history[0]["role"] == "user" and isinstance(agent.history[0]["content"], str)


# ── Pre-retrieval ───────────────────────────────────────────────

def test_retrieved_block_sits_between_context_and_question():
    """
    The server's retrieval goes into the user turn after the [Context] block
    and before the question, and its sources are kept for the API.
    Expected: order Context, Retrieved, question; last_sources set.
    """
    found = Retrieval(block="[Retrieved]\n- SS.2.39 (Ch.2 v.39): text\n[/Retrieved]",
                      sources=({"id": "SS.2.39"},))
    agent = make_agent([text_response("ok")], retrieval=found)
    agent.chat("What is the equation of the apsis?")
    sent = first_user_text(agent.client.requests[0])
    assert sent.index("[Context]") < sent.index("[Retrieved]") < sent.index("What is")
    assert agent.last_sources == [{"id": "SS.2.39"}]


def test_retrieve_for_cites_verses_and_suggests_callable_tools():
    """
    Real retrieval over the corpus: hits are led by their citation ids and
    the suggested tools are dispatchable names.
    Expected: an SS.2.x id for "equation of the apsis" and
    compute_planet_position among the suggested tools.
    """
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    found = retrieve_for("equation of the apsis")
    assert any(s["id"].startswith("SS.2.") for s in found.sources)
    assert "compute_planet_position" in found.tools
    assert all(t in TOOL_FUNCTIONS for t in found.tools)
    assert found.block.startswith("[Retrieved]")


def _boom(*args, **kwargs):
    """Stand-in for a source that cannot be read."""
    raise FileNotFoundError("no corpus")


def test_retrieve_for_survives_broken_sources(monkeypatch):
    """
    Failures in both the verse corpus and the commentary must not fail the turn.
    Expected: an empty Retrieval.
    """
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.corpus import bhashya, retrieve

    monkeypatch.setattr(retrieve, "search", _boom)
    monkeypatch.setattr(bhashya, "search", _boom)
    assert retrieve_for("anything") == Retrieval()


def test_retrieve_for_keeps_verses_when_commentary_is_missing(monkeypatch):
    """
    Without the commentary files the turn still gets its verses.
    Expected: only verse sources, no commentary section.
    """
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.corpus import bhashya

    monkeypatch.setattr(bhashya, "available", lambda: False)
    found = retrieve_for("equation of the apsis")
    assert found.sources and all(s["kind"] == "verse" for s in found.sources)
    assert "Vigyan Bhashya" not in found.block


def test_retrieve_for_adds_labelled_commentary_from_the_verse_chapter():
    """
    With the commentary present, up to two hits follow the verses in their own
    labelled section, taken from the top verse's chapter when it has matches.
    Skipped when the commentary files are not on this machine.
    Expected: commentary sources after verse sources, from Chapter 2 for
    "equation of the apsis", and a block that marks them as commentary.
    """
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.corpus import bhashya

    if not bhashya.available():
        pytest.skip("Vigyan Bhashya files not available")
    found = retrieve_for("equation of the apsis")
    kinds = [s["kind"] for s in found.sources]
    assert "commentary" in kinds and kinds.index("commentary") > kinds.index("verse")
    commentary = [s for s in found.sources if s["kind"] == "commentary"]
    assert len(commentary) <= 2 and all(c["chapter"] == 2 for c in commentary)
    assert "never as the text" in found.block


def test_retrieve_for_answers_hindi_from_the_hindi_commentary():
    """
    A Devanagari question finds no English verses but does reach the Hindi OCR.
    Skipped when the commentary files are not on this machine.
    Expected: SB.hi.* commentary sources only.
    """
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.corpus import bhashya

    if not bhashya.available():
        pytest.skip("Vigyan Bhashya files not available")
    found = retrieve_for("मन्दोच्च क्या है?")
    assert found.sources and all(s["id"].startswith("SB.hi.") for s in found.sources)


def test_last_round_asks_for_an_answer_without_storing_the_note():
    """
    The last round tells the model it may not call tools, but that note is
    not part of the conversation.
    Expected: the final request ends with the tool-limit note, earlier ones
    do not, and no stored history message carries it.
    """
    rounds = SuryaSiddhantaAgent.MAX_TOOL_ROUNDS
    agent = make_agent([tool_response("get_constant", {"constant_name": "kalpa"}, f"c{i}")
                        for i in range(rounds - 1)] + [text_response("Done.")])
    agent.chat("search a lot")
    requests = agent.client.requests
    assert "Tool limit reached" in requests[-1]["messages"][-1]["content"]
    assert all("Tool limit reached" not in str(r["messages"]) for r in requests[:-1])
    assert all("Tool limit reached" not in str(m) for m in agent.history)


def test_tool_call_written_out_as_text_is_not_shown_to_the_user():
    """
    DeepSeek writes ``<｜DSML｜tool_calls>`` markup as plain text when tools
    are off and the host does not parse it; the user must not see that.
    Expected: text before the markup is kept, and a reply that is only
    markup falls back to the tool-limit message instead of leaking.
    """
    markup = '<｜DSML｜tool_calls><｜DSML｜invoke name="search_corpus"></｜DSML｜invoke></｜DSML｜tool_calls>'
    partial = make_agent([text_response(f"The text says X.\n\n{markup}")])
    assert partial.chat("q") == "The text says X."
    only = make_agent([text_response(markup)])
    reply = only.chat("q")
    assert "DSML" not in reply and "tool-call limit" in reply
