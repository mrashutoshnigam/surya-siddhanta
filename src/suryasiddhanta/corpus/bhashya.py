"""Retrieval over the Srivastava *Vigyan Bhashya* -- a modern commentary.

A second source beside `retrieve.py`, deliberately kept apart from it. The
Burgess corpus that `retrieve.py` serves is the text being explained; this is
Mahavir Prasad Srivastava's twentieth-century Hindi commentary *Surya
Siddhanta Vigyan Bhashya* (Vigyan Parishad, Prayag), read from two local
Markdown files:

- English (`SS_BHASHYA_EN_PATH`): a ChatGPT machine translation of the book,
  one `## Source page N` block per scanned page (838 pages).
- Hindi (`SS_BHASHYA_HI_PATH`): the Sarvam AI OCR of the same book, with no
  page markers.

Every record this module returns carries `kind="commentary"`, an `id`
(`SB.en.p<N>` for an English page, `SB.hi.<n>` for a Hindi chunk) and a
`source` naming the commentary and how the text was produced. Callers must
keep the distinction visible: a hit here is what a modern commentator says
*about* the Surya Siddhanta, never the text itself, and should never be
quoted as scripture. Nor should its numbers be relied on: the OCR routinely
reads ९ (9) as ६ (6) (the English dates the commentator's birth to "1644"
for 1944 Vikrama), and the translation carries those errors across. Take
figures from the calculation tools or the Burgess corpus instead.

Copyright: the commentary is a modern, copyrighted work, and both files are
derived from it. They are for local use only. Nothing here may ship in the
PyPI package: this module reads the files from paths outside the repository,
caches the index in the system temp directory, and `pyproject.toml`'s
package-data lists neither the sources nor the cache. Keep it that way.

Search is BM25 over SQLite FTS5 with the `unicode61` tokenizer, which keeps
whole Devanagari words (matras and virama are token characters, the dandas
are separators). Hindi compounds and inflected forms that only begin with
the query word are reached by a prefix query, and words buried inside a
sandhi compound by a trigram table over the Hindi chunks, both tried only
when exact matching finds nothing. No embeddings and no dependencies beyond
the standard library.

    from suryasiddhanta.corpus import bhashya
    bhashya.search("mandocca")          # English pages
    bhashya.search("मन्दोच्च", chapter=2)  # Hindi chunks from Chapter 2
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
import threading
from pathlib import Path
from typing import Any, Iterator

_DEFAULT_EN_PATH = (r"D:\ss_corpus\data\interim\ChatGPT_Translated"
                    r"\Surya_Siddhanta_English_Translation.md")
_DEFAULT_HI_PATH = (r"D:\ss_corpus\data\interim\sarvam_ocr"
                    r"\Surya-siddhanta-Hindi.md")

CONFIG_PATH = Path(__file__).with_name("config") / "bhashya_chapters.json"

SOURCE_EN = ("Srivastava, Surya Siddhanta Vigyan Bhashya "
             "(machine-translated English)")
SOURCE_HI = "Srivastava, Surya Siddhanta Vigyan Bhashya (Sarvam AI OCR, Hindi)"

# Bump when the chunking or the schema changes, so stale caches are rebuilt.
_SCHEMA_VERSION = 1

# A Hindi window holds whole paragraphs up to about this many characters
# (a longer paragraph is cut at line ends, a longer line at a space).
_HINDI_WINDOW = 1500

# Pages and windows with less text than this are blank scans, lone running
# headers or stray page numbers, and are not indexed.
_MIN_CHARS = 60

_COLUMNS = ("id", "kind", "language", "page", "heading", "chapter", "text",
            "verse_marks", "source")

_lock = threading.Lock()
_db_path: Path | None = None
_db_key: str | None = None
_backend: str | None = None


# --- paths and status ---------------------------------------------------------

def _en_path() -> Path:
    """The English translation's path, read from the environment each call.

    Read at call time rather than import time so a test (or a long-running
    server) can point the module somewhere else without reloading it.
    """
    return Path(os.environ.get("SS_BHASHYA_EN_PATH", _DEFAULT_EN_PATH))


def _hi_path() -> Path:
    """The Hindi OCR's path, read from the environment each call."""
    return Path(os.environ.get("SS_BHASHYA_HI_PATH", _DEFAULT_HI_PATH))


def _sources() -> dict[str, Path]:
    """The source files that exist right now, keyed by language code."""
    out = {}
    for language, path in (("en", _en_path()), ("hi", _hi_path())):
        try:
            if path.is_file():
                out[language] = path
        except (OSError, ValueError):
            pass
    return out


def available() -> bool:
    """True when at least one of the two commentary files can be read.

    Never raises: a missing drive or an unreadable path counts as absent.
    `search` and `get_page` simply return nothing for a language whose file
    is missing.
    """
    return bool(_sources())


def backend() -> str:
    """Which sources the last query was answered from.

    Returns "en+hi", "en" or "hi" for the languages indexed in the cache in
    use, "+trigram" appended when the Hindi trigram table was built, or
    "none" before the first query and whenever no source file exists.
    """
    return _backend or "none"


# --- chapter configuration ------------------------------------------------------

def _load_config() -> dict[str, Any]:
    """The hand-checked chapter boundaries, or empty ones if unreadable."""
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"en": {"chapters": []}, "hi": {"boundaries": []}}


def _english_chapter(page: int, ranges: list[dict[str, Any]]) -> int | None:
    """The chapter a scanned page belongs to, or None outside every range."""
    for r in ranges:
        if r["first_page"] <= page <= r["last_page"]:
            return r["chapter"]
    return None


# --- text helpers ---------------------------------------------------------------

_VERSE_MARK = re.compile(r"[।॥]{1,2}\s*(\d{1,3})\s*[।॥]{1,2}")
_FIGURE = re.compile(r"\[Figure:[^\]]*\]", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
# Headings such as "( 23)", "( ৭০)" or "(R)" are the front matter's page
# numbers (the last one misread), OCR'd into markdown headings; they are
# dropped rather than used as headings.
_PAGE_NUMBER = re.compile(r"^(\(\s*\w{1,4}\s*\)|\d+)$")


def _verse_marks(text: str) -> list[int]:
    """Verse numbers closing a Sanskrit verse (`॥N॥`), in order, unique.

    Best effort. `\\d` and `int` accept Devanagari (and the stray Bengali
    digits the OCR emits) as well as ASCII digits. The marks also number
    verses quoted from other works, and the OCR misreads digits, so these
    say which verse numbers appear on a page, not which verses it explains.
    """
    seen: dict[int, None] = {}
    for match in _VERSE_MARK.finditer(text):
        try:
            seen.setdefault(int(match.group(1)), None)
        except ValueError:
            continue
    return list(seen)


def _clean_line(line: str) -> str:
    """A source line with markdown heading marks and trailing breaks removed."""
    heading = _HEADING.match(line)
    return heading.group(2) if heading else line.rstrip()


def _squeeze(text: str) -> str:
    """Collapse runs of blank lines and trim, keeping paragraph breaks."""
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# --- English: one chunk per scanned page ---------------------------------------

def _english_chunks(path: Path, ranges: list[dict[str, Any]]
                    ) -> Iterator[dict[str, Any]]:
    """One record per `## Source page N` block of the English translation.

    `heading` is the last `###` heading at or before the page, carried over
    from earlier pages when the page has none of its own; page-number
    headings are dropped. Code fences are dropped as markup; their contents
    (formulas) are kept as text.
    """
    page: int | None = None
    heading: str | None = None
    lines: list[str] = []

    def flush() -> Iterator[dict[str, Any]]:
        """Yield the page collected so far, unless it is near-empty."""
        if page is None:
            return
        text = _squeeze("\n".join(lines))
        if len(text) < _MIN_CHARS:
            return
        yield {
            "id": f"SB.en.p{page}", "kind": "commentary", "language": "en",
            "page": page, "heading": heading,
            "chapter": _english_chapter(page, ranges), "text": text,
            "verse_marks": _verse_marks(text), "source": SOURCE_EN,
        }

    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            marker = re.match(r"^##\s+Source page\s+(\d+)\s*$", line)
            if marker:
                yield from flush()
                page, lines = int(marker.group(1)), []
                continue
            if line.startswith("```"):
                continue
            sub = re.match(r"^###\s+(.*?)\s*$", line)
            if sub and _PAGE_NUMBER.match(sub.group(1)):
                continue
            if sub and sub.group(1):
                heading = sub.group(1)
            if page is not None:
                lines.append(_clean_line(line))
    yield from flush()


# --- Hindi: heading sections in ~1500-character windows --------------------------

def _windows(paragraphs: list[str], size: int) -> list[str]:
    """Pack whole paragraphs into windows of at most about `size` chars.

    A paragraph longer than `size` is broken at line ends, and a single line
    longer than that at word boundaries, so every window stays near `size`.
    """
    pieces: list[str] = []
    for para in paragraphs:
        if len(para) <= size:
            pieces.append(para)
            continue
        for line in para.split("\n"):
            while len(line) > size:
                cut = line.rfind(" ", 0, size)
                cut = cut if cut > 0 else size
                pieces.append(line[:cut])
                line = line[cut:].lstrip()
            if line:
                pieces.append(line)

    windows: list[str] = []
    current: list[str] = []
    length = 0
    for piece in pieces:
        if current and length + len(piece) > size:
            windows.append("\n\n".join(current))
            current, length = [], 0
        current.append(piece)
        length += len(piece) + 2
    if current:
        windows.append("\n\n".join(current))
    return windows


def _hindi_sections(path: Path, boundaries: list[dict[str, Any]]
                    ) -> Iterator[tuple[int | None, str | None, str]]:
    """Split the OCR into (chapter, heading, text) sections.

    A section starts at every markdown heading and at every chapter anchor
    from the config; the anchors are matched in order, each only after the
    one before it, so earlier tables of contents cannot match. Chapter
    anchors that are plain body lines (Chapters 4, 5, 8 and 14 have no
    heading in the OCR) become the section heading themselves. The heading
    line is kept in the text, because many of the OCR's "headings" are
    misread verse lines that should stay searchable. `[Figure: ...]`
    descriptions (English, written by the OCR model), `---` page rules and
    page-number headings are dropped.
    """
    pending = list(boundaries)
    chapter: int | None = None
    heading: str | None = None
    lines: list[str] = []

    def flush() -> Iterator[tuple[int | None, str | None, str]]:
        """Yield the section collected so far, figures removed."""
        text = _squeeze(_FIGURE.sub("", "\n".join(lines)))
        if text:
            yield chapter, heading, text

    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if line.strip() == "---":
                continue
            cleaned = _clean_line(line).strip()
            if _HEADING.match(line) and _PAGE_NUMBER.match(cleaned):
                continue
            if pending and cleaned == pending[0]["anchor"]:
                yield from flush()
                chapter, heading, lines = pending.pop(0)["chapter"], cleaned, []
            elif _HEADING.match(line) and cleaned:
                yield from flush()
                heading, lines = cleaned, []
            lines.append(_clean_line(line))
    yield from flush()


def _hindi_chunks(path: Path, boundaries: list[dict[str, Any]]
                  ) -> Iterator[dict[str, Any]]:
    """Hindi records: each section cut into windows on paragraph boundaries.

    Ids number the windows in reading order (`SB.hi.1`, `SB.hi.2`, ...), so
    they are stable only while the OCR file and this chunking are unchanged.
    """
    n = 0
    for chapter, heading, text in _hindi_sections(path, boundaries):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for window in _windows(paragraphs, _HINDI_WINDOW):
            if len(window) < _MIN_CHARS:
                continue
            n += 1
            yield {
                "id": f"SB.hi.{n}", "kind": "commentary", "language": "hi",
                "page": None, "heading": heading, "chapter": chapter,
                "text": window, "verse_marks": _verse_marks(window),
                "source": SOURCE_HI,
            }


# --- the SQLite cache -----------------------------------------------------------

def _trigram_supported(con: sqlite3.Connection) -> bool:
    """True if this SQLite build has FTS5's trigram tokenizer (3.34+)."""
    try:
        con.execute("CREATE VIRTUAL TABLE temp.probe USING fts5(x, tokenize='trigram')")
        con.execute("DROP TABLE temp.probe")
        return True
    except sqlite3.Error:
        return False


def _build(destination: Path, sources: dict[str, Path]) -> None:
    """Index the available sources into a fresh SQLite file.

    `chunks` holds the records; `chunks_fts` is the unicode61 BM25 index
    over heading and text; `chunks_tri` is a trigram index over the Hindi
    text only, built when the SQLite library supports it. Diacritics are
    folded so "Surya" matches "Sūrya".
    """
    config = _load_config()
    con = sqlite3.connect(destination)
    try:
        con.execute(
            "CREATE TABLE chunks (rowid INTEGER PRIMARY KEY, id TEXT UNIQUE, "
            "kind TEXT, language TEXT, page INTEGER, heading TEXT, "
            "chapter INTEGER, text TEXT, verse_marks TEXT, source TEXT)")
        con.execute(
            "CREATE VIRTUAL TABLE chunks_fts USING fts5(heading, text, "
            "content='chunks', content_rowid='rowid', "
            "tokenize='unicode61 remove_diacritics 2')")
        trigram = "hi" in sources and _trigram_supported(con)
        if trigram:
            con.execute(
                "CREATE VIRTUAL TABLE chunks_tri USING fts5(text, "
                "content='chunks', content_rowid='rowid', tokenize='trigram')")
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")

        records: list[dict[str, Any]] = []
        if "en" in sources:
            records.extend(_english_chunks(
                sources["en"], config.get("en", {}).get("chapters", [])))
        if "hi" in sources:
            records.extend(_hindi_chunks(
                sources["hi"], config.get("hi", {}).get("boundaries", [])))

        con.executemany(
            "INSERT INTO chunks (id, kind, language, page, heading, chapter, "
            "text, verse_marks, source) VALUES (?,?,?,?,?,?,?,?,?)",
            [(r["id"], r["kind"], r["language"], r["page"], r["heading"],
              r["chapter"], r["text"], json.dumps(r["verse_marks"]),
              r["source"]) for r in records])
        con.execute("INSERT INTO chunks_fts (rowid, heading, text) "
                    "SELECT rowid, coalesce(heading, ''), text FROM chunks")
        if trigram:
            con.execute("INSERT INTO chunks_tri (rowid, text) "
                        "SELECT rowid, text FROM chunks WHERE language='hi'")
        con.execute("CREATE INDEX chunks_page ON chunks(language, page)")

        status = "+".join(lang for lang in ("en", "hi") if lang in sources)
        con.executemany("INSERT INTO meta VALUES (?, ?)",
                        [("backend", status + ("+trigram" if trigram else "")),
                         ("schema", str(_SCHEMA_VERSION))])
        con.commit()
    finally:
        con.close()


def _cache_key(sources: dict[str, Path]) -> tuple[str, str]:
    """(family, version) hashes naming the cache file for these sources.

    The family hashes the source paths, so a test pointing the env vars at
    a temp directory never touches the real cache. The version adds each
    file's size and mtime, the config's, and the schema version, so editing
    any of them builds a new file instead of rewriting one a reader may
    still have open (Windows refuses to replace an open file).
    """
    family = hashlib.sha1(
        "|".join(f"{k}={v.resolve()}" for k, v in sorted(sources.items()))
        .encode("utf-8")).hexdigest()[:12]
    parts = [str(_SCHEMA_VERSION)]
    for path in [*(sources[k] for k in sorted(sources)), CONFIG_PATH]:
        try:
            st = path.stat()
            parts.append(f"{st.st_size}:{st.st_mtime_ns}")
        except OSError:
            parts.append("-")
    version = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return family, version


def _cache_db() -> Path | None:
    """The cache file for the current sources, built on first use.

    Returns None when no source exists. A build writes to a private temp name
    and is then renamed into place, so a concurrent reader never sees a half
    built index; caches of older versions of the same sources are removed
    when possible and otherwise left for the next call.
    """
    global _db_path, _db_key, _backend
    sources = _sources()
    if not sources:
        _db_path = _db_key = _backend = None
        return None

    family, version = _cache_key(sources)
    key = f"{family}_{version}"
    with _lock:
        if _db_key == key and _db_path is not None and _db_path.exists():
            return _db_path

        directory = Path(tempfile.gettempdir())
        target = directory / f"surya_bhashya_{key}.db"
        if not target.exists():
            partial = directory / f"surya_bhashya_{key}.{os.getpid()}.partial"
            try:
                _build(partial, sources)
                os.replace(partial, target)
            finally:
                if partial.exists():
                    partial.unlink()
        for old in directory.glob(f"surya_bhashya_{family}_*.db"):
            if old != target:
                try:
                    old.unlink()
                except OSError:
                    pass

        con = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT value FROM meta WHERE key='backend'").fetchone()
        finally:
            con.close()
        _db_path, _db_key, _backend = target, key, row[0] if row else None
        return target


def _connect() -> sqlite3.Connection | None:
    """A read-only connection to the cache, or None when no source exists."""
    path = _cache_db()
    if path is None:
        return None
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """A result row as a plain record, `verse_marks` decoded to a list."""
    d = {k: row[k] for k in row.keys() if k != "rowid"}
    d["verse_marks"] = json.loads(d.get("verse_marks") or "[]")
    return d


# --- query handling -------------------------------------------------------------

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
# Keep word characters and the Devanagari block (Python's \w misses matras
# and virama), then drop the dandas, which are punctuation to FTS5 as well.
_FTS_SPECIAL = re.compile(r"[^\w\sऀ-ॿ]|[।॥]")

# English stopwords as in retrieve.py, plus the commonest Hindi function
# words, which otherwise match nearly every chunk of the commentary.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "its", "me", "of", "on", "or", "s",
    "tell", "that", "the", "then", "there", "this", "to", "what", "when",
    "where", "which", "who", "why", "with", "was", "were", "you", "your",
    "explain", "describe", "give", "show", "about", "commentary", "say",
    "says", "srivastava",
    "का", "की", "के", "को", "में", "से", "पर", "है", "हैं", "था", "थे", "थी",
    "और", "या", "भी", "तो", "ही", "यह", "वह", "ये", "वे", "इस", "उस", "इन",
    "उन", "एक", "जो", "कि", "क्या", "कैसे", "क्यों", "कब", "कहाँ", "होता",
    "होती", "होते", "गया", "गयी", "गई", "किया", "करना", "करते", "जाता",
    "जाती", "बताइए", "बताओ", "समझाइए",
}


def _terms(query: str) -> list[str]:
    """Content words of a query, lower-cased, stopwords removed.

    Falls back to every word when all of them are stopwords, so a query
    never silently becomes empty.
    """
    cleaned = _FTS_SPECIAL.sub(" ", query).lower()
    words = [w for w in cleaned.split() if len(w) > 1 and w not in _STOPWORDS]
    return words or [w for w in cleaned.split() if w]


def _attempts(terms: list[str]) -> list[str]:
    """FTS5 match expressions, from strictest to loosest.

    Every term must match, then any of them; each tier first exactly and
    then as a prefix (terms of four characters or more), which reaches Hindi
    compounds and inflections that begin with the query word, and English
    plurals. Terms are quoted so user punctuation cannot become FTS5 syntax.
    """
    exact = [f'"{t}"' for t in terms]
    prefix = [f'"{t}"*' if len(t) >= 4 else f'"{t}"' for t in terms]
    out: list[str] = []
    for joiner in (" AND ", " OR "):
        for group in (exact, prefix):
            expression = joiner.join(group)
            if expression not in out:
                out.append(expression)
    return out


def _language_for(query: str) -> str:
    """"hi" when the query contains Devanagari, else "en"."""
    return "hi" if _DEVANAGARI.search(query) else "en"


def search(query: str, language: str | None = None,
           chapter: int | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Full-text search over the commentary, ranked by BM25.

    `language` is "en" (translated pages) or "hi" (OCR chunks); None picks
    "hi" when the query contains Devanagari and "en" otherwise. `chapter`
    restricts hits to one Surya Siddhanta chapter (1-14) as assigned by the
    hand-checked config; front matter and the appendix have no chapter and
    are excluded by any chapter filter.

    Each hit is a record (`id`, `kind`, `language`, `page`, `heading`,
    `chapter`, `text`, `verse_marks`, `source`) plus a `snippet` with the
    match marked `<<` `>>`. Returns [] when the query has no words, when the
    language's source file is missing, or on any SQLite error -- this sits
    behind a chatbot tool and must not raise on bad input.
    """
    terms = _terms(query or "")
    if not terms or limit <= 0:
        return []
    language = language or _language_for(query)
    try:
        con = _connect()
    except (OSError, ValueError, sqlite3.Error):
        return []
    if con is None:
        return []

    filters = " AND c.language = ?"
    args: list[Any] = [language]
    if chapter is not None:
        filters += " AND c.chapter = ?"
        args.append(chapter)

    bm25_sql = (
        "SELECT c.*, snippet(chunks_fts, 1, '<<', '>>', ' ... ', 24) AS snippet "
        "FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid "
        "WHERE chunks_fts MATCH ?" + filters +
        " ORDER BY bm25(chunks_fts, 2.0, 1.0) LIMIT ?")
    trigram_sql = (
        "SELECT c.*, snippet(chunks_tri, 0, '<<', '>>', ' ... ', 24) AS snippet "
        "FROM chunks_tri f JOIN chunks c ON c.rowid = f.rowid "
        "WHERE chunks_tri MATCH ?" + filters +
        " ORDER BY bm25(chunks_tri) LIMIT ?")

    try:
        rows: list[sqlite3.Row] = []
        for match in _attempts(terms):
            rows = con.execute(bm25_sql, (match, *args, limit)).fetchall()
            if rows:
                break
        long_terms = [t for t in terms if len(t) >= 3]
        if not rows and language == "hi" and long_terms and "+trigram" in backend():
            # Trigram matching finds a word inside a sandhi compound, which
            # unicode61 cannot split; it needs three characters per term.
            for joiner in (" AND ", " OR "):
                match = joiner.join(f'"{t}"' for t in long_terms)
                rows = con.execute(trigram_sql, (match, *args, limit)).fetchall()
                if rows:
                    break
        return [_row_to_dict(r) for r in rows]
    except sqlite3.Error:
        return []
    finally:
        con.close()


def get_page(page: int) -> dict[str, Any] | None:
    """One translated page by its scan number (1-838), or None.

    None as well for a near-empty page that was not indexed, and when the
    English file is missing. The Hindi OCR has no page markers, so there is
    no Hindi equivalent.
    """
    try:
        con = _connect()
    except (OSError, ValueError, sqlite3.Error):
        return None
    if con is None:
        return None
    try:
        row = con.execute(
            "SELECT * FROM chunks WHERE language='en' AND page=?",
            (page,)).fetchone()
        return _row_to_dict(row) if row else None
    except sqlite3.Error:
        return None
    finally:
        con.close()


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "mandocca"
    print(f"available={available()}")
    for hit in search(q, limit=5):
        print(f"  {hit['id']:<12} ch={hit['chapter']} {hit['snippet'][:100]!r}")
    print(f"backend={backend()}")
