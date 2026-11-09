"""The bundled book must be complete and reachable by every corpus consumer."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3

import pytest
from fastapi.testclient import TestClient

from suryasiddhanta.corpus import retrieve


CORPUS_PATH = Path(__file__).resolve().parents[1] / "src" / "suryasiddhanta" / "corpus" / "data" / "corpus.json"
CHAPTER_COUNTS = (70, 69, 51, 26, 17, 24, 24, 21, 18, 15, 23, 90, 25, 27)


@pytest.fixture
def corpus(monkeypatch, tmp_path):
    """Use the checked-in export and an isolated cache, never a local pipeline."""
    monkeypatch.setattr(retrieve, "DB_PATH", tmp_path / "missing.db")
    monkeypatch.setattr(retrieve, "JSON_PATH", CORPUS_PATH)
    monkeypatch.setattr(retrieve.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(retrieve, "_local_copy", None)
    monkeypatch.setattr(retrieve, "_backend", None)
    monkeypatch.setattr(retrieve, "_label_counts", None)
    monkeypatch.setattr(retrieve, "_source_key", None, raising=False)
    return retrieve


def _record(text, labels=()):
    return {
        "id": "SS.1.1", "chapter": 1, "verse": 1, "verse_end": None,
        "chapter_name_en": "Mean motions", "chapter_name_iast": "madhyama",
        "translation_en": text, "topics": [], "mcp_tools": list(labels),
        "source": {"en": "test export"}, "flags": [],
    }


def _write_json(path, text, labels=()):
    path.write_text(json.dumps([_record(text, labels)]), encoding="utf-8")


def _load_retrieve():
    spec = importlib.util.spec_from_file_location("isolated_retrieve", retrieve.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundled_corpus_has_every_numbered_verse_once():
    records = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    expected = {
        f"SS.{chapter}.{verse}"
        for chapter, count in enumerate(CHAPTER_COUNTS, 1)
        for verse in range(1, count + 1)
    }
    assert len(records) == 500
    assert Counter(r["chapter"] for r in records) == dict(enumerate(CHAPTER_COUNTS, 1))
    assert {r["id"] for r in records} == expected
    for record in records:
        assert record["id"] == f"SS.{record['chapter']}.{record['verse']}"
        assert record["translation_en"].strip(), record["id"]
        assert record.get("verse_end") in (None, record["verse"]), record["id"]


def test_checkout_defaults_read_the_bundled_export(monkeypatch, tmp_path):
    monkeypatch.delenv("SS_CORPUS_JSON_PATH", raising=False)
    monkeypatch.delenv("SS_CORPUS_DB_PATH", raising=False)
    monkeypatch.setattr(retrieve.tempfile, "gettempdir", lambda: str(tmp_path))
    module = _load_retrieve()
    assert module.JSON_PATH == CORPUS_PATH
    assert module.DB_PATH == CORPUS_PATH.with_suffix(".db")
    assert module.get_verse(11, 1)["id"] == "SS.11.1"


def test_explicit_source_environment_overrides_are_preserved(monkeypatch, tmp_path):
    json_path = tmp_path / "chosen.json"
    db_path = tmp_path / "chosen.db"
    _write_json(json_path, "Chosen export")
    monkeypatch.setenv("SS_CORPUS_JSON_PATH", str(json_path))
    monkeypatch.setenv("SS_CORPUS_DB_PATH", str(db_path))
    monkeypatch.setattr(retrieve.tempfile, "gettempdir", lambda: str(tmp_path))
    module = _load_retrieve()
    assert module.JSON_PATH == json_path
    assert module.DB_PATH == db_path
    assert module.get_verse(1, 1)["translation_en"] == "Chosen export"


@pytest.mark.parametrize("chapter,count", list(enumerate(CHAPTER_COUNTS, 1)))
def test_verse_explorer_returns_complete_chapters(corpus, chapter, count):
    from suryasiddhanta.api.main import app

    with TestClient(app) as client:
        response = client.get(f"/corpus/verses/{chapter}")
    assert response.status_code == 200
    verses = response.json()["verses"]
    assert [v["id"] for v in verses] == [f"SS.{chapter}.{n}" for n in range(1, count + 1)]


def test_rest_exact_lookup_and_search_reach_restored_verses(corpus):
    from suryasiddhanta.api.main import app

    with TestClient(app) as client:
        verse = client.get("/corpus/verse/11/1")
        hits = client.get("/corpus/search", params={"q": "Thine intent"})
        appendix = client.get("/corpus/verse/14/28")
    assert verse.status_code == 200
    assert verse.json()["id"] == "SS.11.1"
    assert hits.status_code == 200
    assert "SS.1.5" in {h["id"] for h in hits.json()["results"]}
    assert appendix.status_code == 404


def test_chat_tools_and_automatic_retrieval_reach_restored_verses(corpus, monkeypatch):
    from suryasiddhanta.chatbot.agent import retrieve_for
    from suryasiddhanta.chatbot.tools import dispatch_tool
    from suryasiddhanta.corpus import bhashya

    # The separate optional commentary source is not part of verse retrieval.
    monkeypatch.setattr(bhashya, "available", lambda: False)
    verse = json.loads(dispatch_tool("get_verse", {"chapter": 11, "verse": 1}))
    hits = json.loads(dispatch_tool("search_corpus", {"query": "Thine intent"}))
    automatic = retrieve_for("Thine intent")
    assert verse["id"] == "SS.11.1"
    assert "SS.1.5" in {h["id"] for h in hits["results"]}
    assert "SS.1.5" in {s["id"] for s in automatic.sources}
    assert "SS.1.5" in automatic.block


def test_json_edit_refreshes_exact_lookup_and_search(corpus, tmp_path, monkeypatch):
    path = tmp_path / "export.json"
    _write_json(path, "Original translation")
    monkeypatch.setattr(corpus, "JSON_PATH", path)
    assert corpus.get_verse(1, 1)["translation_en"] == "Original translation"
    before = path.stat()
    _write_json(path, "Restored new passage")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    assert corpus.get_verse(1, 1)["translation_en"] == "Restored new passage"
    assert corpus.search("Restored")[0]["id"] == "SS.1.1"
    assert corpus.search("Original") == []


def test_switching_to_older_json_export_does_not_reuse_another_export(corpus, tmp_path, monkeypatch):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_json(first, "First export")
    _write_json(second, "Second export")
    os.utime(second, (1, 1))
    monkeypatch.setattr(corpus, "JSON_PATH", first)
    assert corpus.get_verse(1, 1)["translation_en"] == "First export"
    monkeypatch.setattr(corpus, "JSON_PATH", second)
    assert corpus.get_verse(1, 1)["translation_en"] == "Second export"
    # A new process must also select by source identity rather than cache age.
    monkeypatch.setattr(corpus, "_local_copy", None)
    assert corpus.get_verse(1, 1)["translation_en"] == "Second export"


def test_concurrent_cache_publication_reuses_the_completed_index(corpus, tmp_path, monkeypatch):
    """Windows prevents replacement while another request reads the winner."""
    path = tmp_path / "export.json"
    _write_json(path, "Concurrent cold lookup")
    monkeypatch.setattr(corpus, "JSON_PATH", path)

    def another_builder_wins(building, destination):
        # A second builder has published this same source revision. Model the
        # Windows error when its reader holds the completed database open.
        shutil.copyfile(building, destination)
        raise PermissionError("Another reader opened the completed cache")

    monkeypatch.setattr(corpus.os, "replace", another_builder_wins)
    assert corpus.get_verse(1, 1)["translation_en"] == "Concurrent cold lookup"
    assert corpus.search("Concurrent")[0]["id"] == "SS.1.1"
    assert len(list(tmp_path.glob("*.db"))) == 1


def test_label_counts_refresh_without_a_preceding_verse_query(corpus, tmp_path, monkeypatch):
    path = tmp_path / "export.json"
    _write_json(path, "Old labels", ["old"])
    monkeypatch.setattr(corpus, "JSON_PATH", path)
    assert corpus.topic_label_counts() == {"old": 1}
    before = path.stat()
    _write_json(path, "New labels", ["new", "other"])
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    assert corpus.topic_label_counts() == {"new": 1, "other": 1}


def test_indexed_database_has_priority_and_refreshes_after_changes(corpus, tmp_path, monkeypatch):
    path = tmp_path / "export.json"
    db_path = tmp_path / "indexed.db"
    _write_json(path, "Indexed text", ["db_label"])
    monkeypatch.setattr(corpus, "JSON_PATH", path)
    corpus._index_json(db_path)
    _write_json(path, "JSON fallback")
    monkeypatch.setattr(corpus, "DB_PATH", db_path)
    assert corpus.get_verse(1, 1)["translation_en"] == "Indexed text"
    assert corpus.backend() == "sqlite"
    before = db_path.stat()
    with sqlite3.connect(db_path) as con:
        con.execute("UPDATE verses SET translation_en='Changed indexed text'")
    con.close()
    os.utime(db_path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    assert corpus.get_verse(1, 1)["translation_en"] == "Changed indexed text"
    db_path.unlink()
    assert corpus.get_verse(1, 1)["translation_en"] == "JSON fallback"
    assert corpus.backend() == "json"
