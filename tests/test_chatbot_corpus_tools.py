"""Tests for the 5 corpus (book text) tools added to chatbot/tools.py,
wired to suryasiddhanta.corpus.retrieve (reads the live corpus SQLite DB,
path set via the SS_CORPUS_DB_PATH env var, default D:\\ss_corpus\\data\\final).
"""
import json

import pytest

from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS, dispatch_tool

CORPUS_TOOLS = {"get_verse", "get_verses", "search_corpus", "chapter_index", "tools_for_query"}


def test_corpus_tools_registered_in_definitions():
    names = {d["name"] for d in TOOL_DEFINITIONS}
    assert CORPUS_TOOLS <= names


def test_get_verse():
    result = json.loads(dispatch_tool("get_verse", {"chapter": 2, "verse": 39}))
    assert result["id"] == "SS.2.39"
    assert result["chapter"] == 2


def test_get_verse_missing_returns_error_not_exception():
    result = json.loads(dispatch_tool("get_verse", {"chapter": 99, "verse": 99}))
    assert "error" in result


def test_get_verses_chapter_range():
    result = json.loads(dispatch_tool("get_verses", {"chapter": 1, "start": 1, "end": 5}))
    assert result["count"] >= 1
    assert all(v["chapter"] == 1 for v in result["verses"])


def test_search_corpus_returns_cited_results():
    result = json.loads(dispatch_tool("search_corpus", {"query": "equation of the apsis", "limit": 5}))
    assert result["count"] > 0
    for hit in result["results"]:
        assert "id" in hit and "source" in hit


def test_chapter_index():
    result = json.loads(dispatch_tool("chapter_index", {}))
    assert len(result["chapters"]) >= 10


def test_tools_for_query_points_to_calc_tool():
    """
    The bridge from verses to calculations returns names the model can call,
    not the corpus's topic labels.
    Expected: "equation of the apsis" suggests compute_planet_position, and
    every suggestion is a dispatchable tool; the raw labels ride along as topics.
    """
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    result = json.loads(dispatch_tool("tools_for_query", {"query": "equation of the apsis"}))
    assert "compute_planet_position" in result["tools"]
    assert all(name in TOOL_FUNCTIONS for name in result["tools"])
    assert "true_longitude" in result["topics"]


def test_every_corpus_topic_label_maps_to_real_tools():
    """
    Every topic label the corpus pipeline can attach (the rules in
    mcp_tool_map.json) has an entry in TOPIC_TO_TOOLS naming real tools.
    Offline: reads the packaged map, not the corpus.
    Expected: no label missing from the map, no mapped name undispatchable.
    """
    from pathlib import Path

    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS, TOPIC_TO_TOOLS
    import suryasiddhanta.corpus as corpus_pkg

    rules = json.loads((Path(corpus_pkg.__file__).parent / "config" / "mcp_tool_map.json")
                       .read_text(encoding="utf-8"))["rules"]
    labels = {rule["tool"] for rule in rules}
    assert labels <= set(TOPIC_TO_TOOLS), labels - set(TOPIC_TO_TOOLS)
    unknown = {n for names in TOPIC_TO_TOOLS.values() for n in names if n not in TOOL_FUNCTIONS}
    assert not unknown


def test_suggested_tools_drops_unknown_and_keeps_order():
    """
    Translation keeps rank order, removes duplicates, passes real tool names
    through and drops labels nothing implements; every label's primary tool
    comes before any label's alternates.
    Expected: both primaries, then conjunction's alternate; "nonsense" dropped.
    """
    from suryasiddhanta.chatbot.tools import suggested_tools

    names = suggested_tools(["conjunction", "nonsense", "conjunction", "compute_ayanamsha"], top_n=10)
    assert names == ["find_conjunctions", "compute_ayanamsha", "find_star_conjunction"]


def test_retrieval_names_the_source_it_is_reading():
    """
    The pipeline leaves an empty .db between OCR runs, which used to make
    every corpus tool fail with "no such table: verses". Retrieval now falls
    back to the JSON export. Expected: a named backend, never "none" once a
    query has run, and the same records either way.
    """
    from suryasiddhanta.corpus import retrieve

    retrieve.get_verse(2, 39)
    assert retrieve.backend() in ("sqlite", "json")


def test_chapter_twelve_verses_are_retrievable():
    """
    Chapter 12 is the newest chapter implemented and the one whose catalog
    cites verses most heavily, so its records must actually come back.
    Expected: v.85 stating the Moon's orbit of 324,000 yojanas.
    """
    result = json.loads(dispatch_tool("get_verse", {"chapter": 12, "verse": 85}))
    assert result["id"] == "SS.12.85"
    # The scan wraps mid-phrase, so compare on normalised whitespace.
    text = " ".join(result["translation_en"].split())
    assert "three hundred and twenty-four thousand yojanas" in text


def test_search_snippet_marks_the_matched_terms():
    """
    search() promises a snippet showing the match, which the FTS5 table's
    column order determines. Expected: the delimiters around a hit in the
    verse translation, so a fallback-built index is not silently snippeting
    the wrong column.
    """
    result = json.loads(dispatch_tool("search_corpus", {"query": "yojanas orbit", "limit": 5}))
    assert result["count"] > 0
    assert any("<<" in hit.get("snippet", "") for hit in result["results"])


def test_dispatch_unknown_tool():
    result = json.loads(dispatch_tool("no_such_tool", {}))
    assert "error" in result


def test_search_ignores_request_verbs_and_fills_past_a_single_hit():
    """
    "computed" is the user's request, not the verse's wording; with it in an
    AND match only Burgess's long appendix matched, which then stood in for
    the whole answer. Request verbs are now stopwords, the index stems, and a
    short strict result is filled from looser matches.
    Expected: a Chapter 4 (lunar eclipse) verse first, and a full page of hits.
    """
    from suryasiddhanta.corpus import retrieve

    hits = retrieve.search("How is the duration of a lunar eclipse computed?", limit=4)
    assert hits[0]["chapter"] == 4
    assert len(hits) == 4


def test_topic_label_counts_cover_the_corpus_labels():
    """
    Label frequencies used to weight tool suggestions are counted from the corpus.
    Expected: "conjunction" is among the most common labels and every count is positive.
    """
    from suryasiddhanta.corpus import retrieve

    counts = retrieve.topic_label_counts()
    assert counts and all(n > 0 for n in counts.values())
    assert counts["conjunction"] >= counts.get("eclipse_projection", 0)


def test_search_bhashya_registered():
    """
    The commentary search is offered to the model and dispatchable.
    Expected: search_bhashya in TOOL_DEFINITIONS and TOOL_FUNCTIONS.
    """
    from suryasiddhanta.chatbot.tools import TOOL_FUNCTIONS

    assert "search_bhashya" in {d["name"] for d in TOOL_DEFINITIONS}
    assert "search_bhashya" in TOOL_FUNCTIONS


def test_search_bhashya_returns_labelled_commentary():
    """
    Hits are marked as commentary with their own ids and source, Devanagari
    queries reach the Hindi OCR, and each text is clipped for the model.
    Skipped when the commentary files are not on this machine.
    Expected: kind "commentary", SB.hi ids for a Hindi query, text <= cap + 4.
    """
    from suryasiddhanta.chatbot.tools import _BHASHYA_TEXT_CHARS
    from suryasiddhanta.corpus import bhashya

    if not bhashya.available():
        pytest.skip("Vigyan Bhashya files not available")
    result = json.loads(dispatch_tool("search_bhashya", {"query": "मन्दोच्च", "limit": 3}))
    assert result["count"] > 0
    for hit in result["results"]:
        assert hit["kind"] == "commentary"
        assert hit["id"].startswith("SB.hi.")
        assert "Vigyan Bhashya" in hit["source"]
        assert len(hit["text"]) <= _BHASHYA_TEXT_CHARS + 4


def test_search_bhashya_reports_missing_files(monkeypatch):
    """
    Without the commentary files the tool says so instead of raising.
    Expected: an "error" key and an empty result list.
    """
    from suryasiddhanta.corpus import bhashya

    monkeypatch.setattr(bhashya, "available", lambda: False)
    result = json.loads(dispatch_tool("search_bhashya", {"query": "mandocca"}))
    assert "error" in result and result["results"] == []


# ── Clipped results ─────────────────────────────────────────────

#: The agent's per-result budget (agent.SuryaSiddhantaAgent.MAX_TOOL_RESULT_CHARS).
TOOL_RESULT_BUDGET = 12_000


def test_clip_record_cuts_long_text_and_says_so():
    """
    A record's long text fields are cut and marked; short and empty ones are
    left alone or dropped.
    Expected: translation clipped with a length marker and listed in
    ``clipped``, commentary clipped to half, the empty Hindi field gone, the
    id untouched.
    """
    from suryasiddhanta.chatbot.tools import _clip_record

    record = {"id": "SS.1.1", "translation_en": "x" * 1000, "commentary_en": "y" * 1000,
              "translation_hi": "", "sanskrit_iast": "short"}
    out = _clip_record(record, 100)
    assert out["id"] == "SS.1.1" and out["sanskrit_iast"] == "short"
    assert "translation_hi" not in out
    assert out["translation_en"].startswith("x" * 100) and "[clipped, 1,000 characters]" in out["translation_en"]
    assert out["commentary_en"].startswith("y" * 50) and not out["commentary_en"].startswith("y" * 51)
    assert out["clipped"] == ["translation_en", "commentary_en"]


def test_clip_record_leaves_a_short_record_whole():
    """
    A record with nothing over the limit gets no ``clipped`` marker.
    Expected: same text, no ``clipped`` key, and drop-listed fields removed.
    """
    from suryasiddhanta.chatbot.tools import _clip_record

    out = _clip_record({"id": "SS.1.2", "translation_en": "short", "flags": ["no_hindi"]}, 100, drop=("flags",))
    assert out == {"id": "SS.1.2", "translation_en": "short"}


def test_search_corpus_fits_the_model_budget_with_every_hit():
    """
    The model must see every hit of a search, not the first few and a cut-off.
    A gnomon query used to return ~148 KB, of which the model saw 3 of 8 hits.
    Expected: 8 hits, the whole JSON inside the tool-result budget, with and
    without commentary.
    """
    query = {"query": "gnomon shadow gives time of day", "limit": 8}
    for extra in ({}, {"include_commentary": True}):
        raw = dispatch_tool("search_corpus", {**query, **extra})
        assert len(raw) <= TOOL_RESULT_BUDGET
        assert json.loads(raw)["count"] == 8


def test_search_corpus_leaves_commentary_out_by_default():
    """
    Burgess's commentary is long, so a search omits it unless asked.
    Expected: no commentary_en on any default hit; with include_commentary
    some hit carries it, clipped.
    """
    query = {"query": "equation of the apsis", "limit": 5}
    plain = json.loads(dispatch_tool("search_corpus", query))["results"]
    assert not any("commentary_en" in hit for hit in plain)
    rich = json.loads(dispatch_tool("search_corpus", {**query, "include_commentary": True}))["results"]
    assert any("commentary_en" in hit for hit in rich)


def test_get_verses_range_fits_the_model_budget():
    """
    A ten-verse range, which the tool description allows, comes back whole.
    Expected: every verse of Ch.3 v.1-10 present inside the tool-result budget.
    """
    raw = dispatch_tool("get_verses", {"chapter": 3, "start": 1, "end": 10})
    assert len(raw) <= TOOL_RESULT_BUDGET
    verses = json.loads(raw)["verses"]
    assert verses and all(v["chapter"] == 3 for v in verses)


def test_get_verse_clips_an_appendix_sized_record():
    """
    Burgess's appendix is commentary after SS.14.27, and would swamp the
    model's budget if sent whole.
    Expected: the record is returned clipped and marked, well under budget.
    """
    raw = dispatch_tool("get_verse", {"chapter": 14, "verse": 27})
    result = json.loads(raw)
    assert result["id"] == "SS.14.27"
    assert result.get("clipped") and len(raw) < TOOL_RESULT_BUDGET
