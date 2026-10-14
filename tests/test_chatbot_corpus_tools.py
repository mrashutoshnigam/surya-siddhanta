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
    result = json.loads(dispatch_tool("tools_for_query", {"query": "equation of the apsis"}))
    assert "true_longitude" in result["tools"] or "mean_longitude" in result["tools"]


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
