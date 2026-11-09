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

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

# A source checkout carries its own complete export. Deployments and external
# corpus pipelines can still select their own files through the environment.
_BUNDLED_CORPUS = Path(__file__).resolve().parent / "data"
DB_PATH = Path(os.environ.get(
    "SS_CORPUS_DB_PATH",
    str(_BUNDLED_CORPUS / "corpus.db"),
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
    str(_BUNDLED_CORPUS / "corpus.json"),
))

_JSON_FIELDS = ("topics", "mcp_tools", "source", "flags")

_COLUMNS = (
    "id", "chapter", "verse", "verse_end", "chapter_name_en",
    "chapter_name_iast", "sanskrit_devanagari", "sanskrit_iast",
    "translation_en", "translation_hi", "commentary_en", "commentary_hi",
    "topics", "mcp_tools", "source", "flags",
)

#: Bump when _index_json's schema changes, so stale caches are rebuilt.
_JSON_INDEX_VERSION = 2

_local_copy: Path | None = None
_backend: str | None = None
_source_key: tuple[str, str, int, int, int] | None = None


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
        # Porter stemming lets "computed" match "compute" and "eclipses"
        # match "eclipse"; the pipeline's own index may not stem, so search
        # below must not depend on it.
        con.execute(
            "CREATE VIRTUAL TABLE verses_fts USING fts5("
            "id UNINDEXED, translation_en, commentary_en, topics, "
            "tokenize='porter unicode61')")

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

    The indexed database is preferred and copied to temp. Each cache belongs
    to one resolved source path, modification time, size and index version,
    so another export (even an older one) cannot reuse its contents.
    """
    global _local_copy, _backend, _source_key, _label_counts

    if _is_indexed(DB_PATH):
        source, kind = DB_PATH, "sqlite"
    elif JSON_PATH.exists():
        source, kind = JSON_PATH, "json"
    else:
        raise FileNotFoundError(
            f"No usable corpus: {DB_PATH} holds no verses table and "
            f"{JSON_PATH} does not exist. Set SS_CORPUS_DB_PATH or "
            f"SS_CORPUS_JSON_PATH.")

    stat = source.stat()
    key = (kind, str(source.resolve()), stat.st_mtime_ns, stat.st_size,
           _JSON_INDEX_VERSION)
    digest = hashlib.sha256(json.dumps(key).encode("utf-8")).hexdigest()[:24]
    tmp = Path(tempfile.gettempdir()) / (
        f"surya_siddhanta_{kind}_cache_v{_JSON_INDEX_VERSION}_{digest}.db")
    if not tmp.exists():
        # Publish only complete databases: concurrent readers must never open
        # an index while another request or process is still writing it.
        with tempfile.NamedTemporaryFile(dir=tmp.parent, suffix=".db", delete=False) as file:
            building = Path(file.name)
        try:
            if kind == "sqlite":
                shutil.copyfile(source, building)
            else:
                _index_json(building)
            try:
                os.replace(building, tmp)
            except OSError:
                # Another builder may have published this identical source
                # revision while we indexed it. Windows cannot replace its
                # cache while a reader holds SQLite open; reuse that complete
                # index, but propagate failures when no usable winner exists.
                if not _is_indexed(tmp):
                    raise
        finally:
            building.unlink(missing_ok=True)
    if _source_key != key:
        _label_counts = None
    _source_key, _local_copy, _backend = key, tmp, kind
    return tmp


def _connect() -> sqlite3.Connection:
    """Open the corpus read-only.

    The DB is copied to local temp for each source revision: SQLite needs
    byte-range locks that many mounted/network filesystems refuse. When the database
    is empty the copy is built from the JSON export instead -- see `backend`.
    """
    path = _corpus_db()
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
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
    # Words that say what the user wants done, not what the verse is about.
    # Left in, they force an AND match on wording the translation never uses.
    "compute", "computed", "computes", "computing", "calculate", "calculated",
    "calculation", "find", "found", "determine", "determined", "obtain",
    "obtained", "get", "many", "much", "please", "according", "text", "says",
    "say", "surya", "siddhanta",
}


def _terms(query: str) -> list[str]:
    cleaned = _FTS_SPECIAL.sub(" ", query).lower()
    words = [w for w in cleaned.split() if len(w) > 1 and w not in _STOPWORDS]
    return words or [w for w in cleaned.split() if w]     # never return nothing


# --- query expansion -----------------------------------------------------------
#
# Burgess translates most technical terms ("sine", "apsis", "ascendant") while
# users often type the Sanskrit ("jya", "mandocca", "lagna"), or the reverse,
# and BM25 only matches words that are there. The app's glossary already
# lists each term with its English and spelling variants as `aliases`; every
# term plus its aliases is one synonym group. The handful below cover terms
# the glossary does not carry. Expansion is used only on the OR fallback, so
# a query that matches as typed is ranked exactly as before.

GLOSSARY_PATH = Path(__file__).resolve().parent.parent / "data" / "glossary.json"

_EXTRA_SYNONYMS = (
    ("jya", "sine", "r-sine", "jiva"),
    ("utkrama jya", "versed sine", "versine"),
    ("mandocca", "apsis", "apogee", "apsides"),
    ("manda", "equation of the centre", "equation of the center", "equation of the apsis"),
    ("sighra", "equation of the conjunction"),
    ("kranti", "declination"),
    ("vikshepa", "celestial latitude", "latitude"),
    ("chaya", "shadow"),
    ("sanku", "gnomon"),
    ("grahana", "eclipse"),
)

_synonym_index: dict[str, frozenset[str]] | None = None


def _fold(text: str) -> str:
    """Lowercase and drop diacritics, so "ayanāṃśa" and "ayanamsa" compare equal."""
    import unicodedata
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())


def _synonyms() -> dict[str, frozenset[str]]:
    """Each folded term or alias -> its whole synonym group (built once)."""
    global _synonym_index
    if _synonym_index is None:
        groups = [tuple(group) for group in _EXTRA_SYNONYMS]
        try:
            terms = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))["terms"]
            groups += [(t["term"], *t.get("aliases", [])) for t in terms.values()]
        except (OSError, ValueError, KeyError):
            pass                                       # expansion is best-effort
        index: dict[str, set[str]] = {}
        for group in groups:
            members = {_fold(m) for m in group if m and len(_fold(m)) > 2}
            for member in members:
                index.setdefault(member, set()).update(members)
        _synonym_index = {k: frozenset(v) for k, v in index.items()}
    return _synonym_index


def _synonyms_of(term: str, cap: int = 6) -> list[str]:
    """FTS5-safe synonyms of one query word, excluding the word itself."""
    group = _synonyms().get(_fold(term), frozenset())
    out = [p for p in (_FTS_SPECIAL.sub(" ", s).strip() for s in sorted(group))
           if p and p != term]
    return out[:cap]


def _expansions(query: str, cap: int = 12) -> list[str]:
    """
    Synonyms of the terms and phrases in a query, as FTS5-safe phrases.

    Matches whole words or whole phrases only ("sine" does not expand
    "cosine"), never returns the query's own terms, and caps the list so a
    long question cannot balloon the MATCH expression.
    """
    folded = f" {_fold(_FTS_SPECIAL.sub(' ', query))} "
    present = set(_terms(query))
    out: list[str] = []
    for member, group in _synonyms().items():
        if f" {member} " not in folded:
            continue
        for synonym in sorted(group):
            phrase = _FTS_SPECIAL.sub(" ", synonym).strip()
            if phrase and phrase not in present and phrase not in out and synonym != member:
                out.append(phrase)
    return out[:cap]


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
    # Narrowest first: every word as typed; then every word or one of its
    # synonyms (("jya" OR "sine") AND "table"); then any word; then any word
    # or any synonym of the query's terms and phrases. Synonyms join only
    # after the as-typed match fails, so they can widen recall but never
    # reorder a query that already matches.
    grouped = [
        "(" + " OR ".join([f'"{t}"'] + [f'"{s}"' for s in _synonyms_of(t)]) + ")"
        if _synonyms_of(t) else f'"{t}"'
        for t in terms
    ]
    widened = quoted + [f'"{p}"' for p in _expansions(query)]
    attempts = list(dict.fromkeys([
        " AND ".join(quoted), " AND ".join(grouped),
        " OR ".join(quoted), " OR ".join(widened),
    ]))

    sql = ("SELECT v.*, snippet(verses_fts, 1, '<<', '>>', ' ... ', 20) AS snippet "
           "FROM verses_fts f JOIN verses v ON v.id = f.id "
           "WHERE verses_fts MATCH ? ORDER BY bm25(verses_fts) LIMIT ?")

    con = _connect()
    try:
        # Take the narrowest attempt's hits first, then fill up to `limit`
        # from the looser ones: one strict hit (often a long appendix that
        # contains every word) must not stand in for the whole answer.
        rows: list[sqlite3.Row] = []
        seen: set[str] = set()
        for match in attempts:
            for row in con.execute(sql, (match, limit)).fetchall():
                if row["id"] not in seen:
                    seen.add(row["id"])
                    rows.append(row)
            if len(rows) >= limit:
                break
        out = [_row_to_dict(r) for r in rows[:limit]]
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


_label_counts: dict[str, int] | None = None


def topic_label_counts() -> dict[str, int]:
    """
    How many records carry each `mcp_tools` label, cached per source revision.

    Lets a caller weight labels by rarity: "conjunction" tags 72 verses
    (most of them about the sighra, not planetary conjunctions), so a hit
    on it says less than one on "true_longitude".
    """
    global _label_counts
    _corpus_db()
    if _label_counts is None:
        con = _connect()
        try:
            counts: dict[str, int] = {}
            for (raw,) in con.execute("SELECT mcp_tools FROM verses"):
                for label in json.loads(raw or "[]"):
                    counts[label] = counts.get(label, 0) + 1
        finally:
            con.close()
        _label_counts = counts
    return _label_counts


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
