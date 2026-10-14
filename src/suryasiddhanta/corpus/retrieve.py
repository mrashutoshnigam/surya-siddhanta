"""Retrieval layer for the Surya Siddhanta chatbot.

This is the module your web app imports. It is deliberately small: four
functions, no framework, no network. Wire these as the tool definitions you
hand to the LLM alongside the calculation tools.

    from retrieve import get_verse, get_verses, search, chapter_index

Design note -- why the model never sees raw text without an id: every function
returns records carrying `id` and `source`. That makes citation mechanical
rather than something the model has to remember to do, which is the single
biggest source of made-up references in scripture bots.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

# The corpus DB is still built by the ss_corpus pipeline, which is under
# active OCR work at a separate location. Default to that live path; once
# the pipeline's data/ is physically merged in here, drop the env var and
# point straight at "data" / "final" / "surya_siddhanta.db" next to this file.
DB_PATH = Path(os.environ.get(
    "SS_CORPUS_DB_PATH",
    r"D:\ss_corpus\data\final\surya_siddhanta.db",
))

# The same pipeline emits the corpus as JSON before it indexes it, and that
# file is often the only one that is actually populated -- the .db is left as
# an empty placeholder between OCR runs. When that happens every retrieval
# tool fails with "no such table: verses", which silently costs the chatbot
# its ability to cite anything at all. So fall back to the JSON, indexing it
# into a local SQLite file with the same schema and the same FTS5 table: the
# four functions below then work unchanged, BM25 ranking and snippets
# included, and neither they nor their callers need to know which source is
# in use. `backend()` reports which one it was.
JSON_PATH = Path(os.environ.get(
    "SS_CORPUS_JSON_PATH",
    r"D:\ss_corpus\data\final\corpus.json",
))

_JSON_FIELDS = ("topics", "mcp_tools", "source", "flags")

_COLUMNS = (
    "id", "chapter", "verse", "verse_end", "chapter_name_en",
    "chapter_name_iast", "sanskrit_devanagari", "sanskrit_iast",
    "translation_en", "translation_hi", "commentary_en", "commentary_hi",
    "topics", "mcp_tools", "source", "flags",
)

_local_copy: Path | None = None
_backend: str | None = None


def backend() -> str:
    """Which source the retrieval layer is reading.

    Returns "sqlite" when the pipeline's indexed database is usable, "json"
    when it was empty or missing and the corpus was rebuilt from the JSON
    export, or "none" before the first query.
    """
    return _backend or "none"


def _is_indexed(path: Path) -> bool:
    """True if a SQLite file exists and actually holds the verses table."""
    if not path.exists():
        return False
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return False
    try:
        return con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='verses'"
        ).fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        con.close()


def _index_json(destination: Path) -> None:
    """Build a corpus database from the JSON export.

    Reproduces the schema the pipeline's own indexer produces, so every query
    in this module runs against it verbatim. The FTS5 table puts the verse
    translation in column 1, which is the column `search` snippets.
    """
    records = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if destination.exists():
        destination.unlink()

    con = sqlite3.connect(destination)
    try:
        con.execute(
            "CREATE TABLE verses (%s)" % ", ".join(
                f"{name} INTEGER" if name in ("chapter", "verse", "verse_end")
                else f"{name} TEXT" for name in _COLUMNS))
        con.execute(
            "CREATE VIRTUAL TABLE verses_fts USING fts5("
            "id UNINDEXED, translation_en, commentary_en, topics)")

        rows = []
        for record in records:
            row = []
            for name in _COLUMNS:
                value = record.get(name)
                row.append(json.dumps(value, ensure_ascii=False)
                           if name in _JSON_FIELDS else value)
            rows.append(row)

        con.executemany(
            "INSERT INTO verses VALUES (%s)" % ",".join("?" * len(_COLUMNS)),
            rows)
        con.executemany(
            "INSERT INTO verses_fts VALUES (?,?,?,?)",
            [(r.get("id"), r.get("translation_en") or "",
              r.get("commentary_en") or "", " ".join(r.get("topics") or []))
             for r in records])
        con.execute("CREATE INDEX verses_chapter ON verses(chapter, verse)")
        con.commit()
    finally:
        con.close()


def _corpus_db() -> Path:
    """The local SQLite file to read, building it from JSON if need be.

    The indexed database is preferred and simply copied to temp. The JSON
    fallback is rebuilt whenever the export is newer than the copy, so an OCR
    run that refreshes the corpus is picked up without a manual step.
    """
    global _local_copy, _backend

    if _is_indexed(DB_PATH):
        tmp = Path(tempfile.gettempdir()) / "surya_siddhanta_cache.db"
        if _local_copy != tmp or not tmp.exists():
            shutil.copyfile(DB_PATH, tmp)
        _local_copy, _backend = tmp, "sqlite"
        return tmp

    if not JSON_PATH.exists():
        raise FileNotFoundError(
            f"No usable corpus: {DB_PATH} holds no verses table and "
            f"{JSON_PATH} does not exist. Set SS_CORPUS_DB_PATH or "
            f"SS_CORPUS_JSON_PATH.")

    tmp = Path(tempfile.gettempdir()) / "surya_siddhanta_json_cache.db"
    stale = (not tmp.exists()
             or tmp.stat().st_mtime < JSON_PATH.stat().st_mtime)
    if stale:
        _index_json(tmp)
    _local_copy, _backend = tmp, "json"
    return tmp


def _connect() -> sqlite3.Connection:
    """Open the corpus read-only.

    The DB is copied to local temp on first use: SQLite needs byte-range locks
    that many mounted/network filesystems refuse. When the pipeline's database
    is empty the copy is built from the JSON export instead -- see `backend`.
    """
    global _local_copy
    if _local_copy is None or not _local_copy.exists():
        _corpus_db()
    con = sqlite3.connect(f"file:{_local_copy}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for f in _JSON_FIELDS:
        if f in d and isinstance(d[f], str):
            d[f] = json.loads(d[f])
    return d


# --- tool 1: exact lookup ----------------------------------------------------

def get_verse(chapter: int, verse: int) -> dict[str, Any] | None:
    """Return one verse by chapter and number. Use this whenever the user
    names a verse -- never let the model recall verse text from memory."""
    con = _connect()
    try:
        row = con.execute(
            "SELECT * FROM verses WHERE chapter=? AND (verse=? OR "
            "(verse<=? AND verse_end>=?))", (chapter, verse, verse, verse)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        con.close()


def get_verses(chapter: int, start: int | None = None,
               end: int | None = None) -> list[dict[str, Any]]:
    """Return a chapter, or a verse range within it."""
    con = _connect()
    try:
        sql = "SELECT * FROM verses WHERE chapter=?"
        args: list[Any] = [chapter]
        if start is not None:
            sql += " AND verse >= ?"
            args.append(start)
        if end is not None:
            sql += " AND verse <= ?"
            args.append(end)
        sql += " ORDER BY verse"
        return [_row_to_dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


# --- tool 2: search ----------------------------------------------------------

_FTS_SPECIAL = re.compile(r'[^\w\sऀ-ॿ]')

# Without this, "how is the moon's parallax computed" ranks every verse
# containing "the" above the ones actually about parallax.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "its", "me", "of", "on", "or", "s",
    "tell", "that", "the", "then", "there", "this", "to", "what", "when",
    "where", "which", "who", "why", "with", "was", "were", "you", "your",
    "explain", "describe", "give", "show", "about",
}


def _terms(query: str) -> list[str]:
    cleaned = _FTS_SPECIAL.sub(" ", query).lower()
    words = [w for w in cleaned.split() if len(w) > 1 and w not in _STOPWORDS]
    return words or [w for w in cleaned.split() if w]     # never return nothing


def search(query: str, limit: int = 8,
           include_commentary: bool = True) -> list[dict[str, Any]]:
    """Full-text search across verse text, commentary and topic labels.

    Returns records ranked by BM25, each with a `snippet` showing the match.
    Set include_commentary=False to restrict to scripture only -- useful when
    the user asks "what does the text actually say", as opposed to "what does
    this mean".
    """
    terms = _terms(query)
    if not terms:
        return []
    # Quote each term so user punctuation can't become FTS5 syntax.
    quoted = [f'"{t}"' for t in terms]
    # Require all content words first; fall back to ANY if that is too narrow.
    attempts = [" AND ".join(quoted), " OR ".join(quoted)]

    sql = ("SELECT v.*, snippet(verses_fts, 1, '<<', '>>', ' ... ', 20) AS snippet "
           "FROM verses_fts f JOIN verses v ON v.id = f.id "
           "WHERE verses_fts MATCH ? ORDER BY bm25(verses_fts) LIMIT ?")

    con = _connect()
    try:
        rows: list[sqlite3.Row] = []
        for match in attempts:
            rows = con.execute(sql, (match, limit)).fetchall()
            if rows:
                break
        out = [_row_to_dict(r) for r in rows]
        if not include_commentary:
            for r in out:
                r.pop("commentary_en", None)
                r.pop("commentary_hi", None)
        return out
    finally:
        con.close()


# --- tool 3: navigation ------------------------------------------------------

def chapter_index() -> list[dict[str, Any]]:
    """Chapter list with verse counts and topic labels -- good for grounding
    'what does the Surya Siddhanta cover?' without dumping the whole corpus."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT chapter, chapter_name_en, chapter_name_iast, COUNT(*) AS verses "
            "FROM verses GROUP BY chapter ORDER BY chapter").fetchall()
        out = []
        for r in rows:
            topics = con.execute(
                "SELECT topics FROM verses WHERE chapter=?", (r["chapter"],)).fetchall()
            flat = sorted({t for row in topics for t in json.loads(row["topics"])})
            out.append({**dict(r), "topics": flat})
        return out
    finally:
        con.close()


# --- tool 4: bridge to the calculation server --------------------------------

def tools_for_query(query: str, limit: int = 5, top_n: int = 4) -> list[str]:
    """Which of your MCP calculation tools the relevant verses point to.

    Call this before answering a computational question: it tells the model
    which function the text itself authorises, so the answer cites the rule it
    is applying instead of inventing a method.

    Ranked by how many of the top hits agree, then truncated -- a summary verse
    that touches every subject in the book should not nominate every tool.
    """
    from collections import Counter
    votes: Counter[str] = Counter()
    for rank, hit in enumerate(search(query, limit=limit)):
        weight = limit - rank                      # earlier hits count for more
        for tool in hit.get("mcp_tools", []):
            votes[tool] += weight
    return [t for t, _ in votes.most_common(top_n)]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "equation of the apsis"
    print(f"--- get_verse(2, 39) ---")
    v = get_verse(2, 39)
    print(f"{v['id']}: {v['translation_en'][:150]}...\n")
    print(f"--- search({q!r}) ---")
    for r in search(q, limit=5):
        print(f"  {r['id']:<10} {r['snippet'][:110]}")
    print(f"\n--- tools_for_query({q!r}) ---")
    print(" ", tools_for_query(q))
