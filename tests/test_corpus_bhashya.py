"""Tests for suryasiddhanta.corpus.bhashya, the Srivastava Vigyan Bhashya source.

Two groups. The offline tests need nothing outside the repository: they check
the hand-curated chapter config, the missing-file behaviour, and the chunking
and search on small synthetic sources written to a temp directory. The live
tests read the two commentary files from SS_BHASHYA_EN_PATH and
SS_BHASHYA_HI_PATH (the ss_corpus pipeline's interim outputs) and are skipped
when those files are absent, as on any machine but the author's.
"""
import json
import os
import re
import tempfile
from pathlib import Path

import pytest

from suryasiddhanta.corpus import bhashya

REPO_ROOT = Path(__file__).resolve().parents[1]

live = pytest.mark.skipif(
    not (bhashya._en_path().is_file() and bhashya._hi_path().is_file()),
    reason="Vigyan Bhashya source files not present (SS_BHASHYA_EN_PATH, "
           "SS_BHASHYA_HI_PATH)")


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Point the module's cache directory at a per-test temp directory.

    Keeps index files built from synthetic sources out of the system temp
    directory, and is torn down with the test.
    """
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(cache))
    return cache


@pytest.fixture
def synthetic_sources(tmp_path, monkeypatch, isolated_cache):
    """Write a three-page English file and a two-chapter Hindi file, and
    point the env vars at them.

    English page 2 is near-empty (a lone running header) and must be skipped;
    page 24 falls in Chapter 1 of the real config. The Hindi file opens with
    front matter, then the Chapter 1 and Chapter 2 anchors from the config.
    """
    en = tmp_path / "en.md"
    en.write_text(
        "# Title\n\n"
        "## Source page 1\n\n"
        "### ( 23)\n"
        "Front matter about Brahmagupta and the date of the text, long enough "
        "to be indexed as a page of its own.\n\n"
        "## Source page 2\n\n"
        "Chapter 763\n\n"
        "## Source page 24\n\n"
        "### Chapter on Mean Motions\n"
        "The mandocca of the Sun is described here in plain words.\n"
        "> सूर्यस्य मन्दोच्चं श्लोकः ॥१॥\n"
        "> अपरः श्लोकः ॥ २ ॥\n",
        encoding="utf-8")
    hi = tmp_path / "hi.md"
    filler = "यह अनुच्छेद केवल परीक्षण के लिए लिखा गया है और इसमें कोई गणना नहीं है। "
    hi.write_text(
        "## भूमिका\n\n" + filler * 3 + "\n\n"
        "## प्रथम अध्याय\n\n"
        "## मध्यमाधिकार\n\n"
        "मन्दोच्च की गति बहुत धीमी है और यह बात इस अध्याय में बतलाई गयी है । ॥२८॥\n\n"
        "[Figure: An English description of a diagram that must not be indexed.]\n\n"
        + "\n\n".join([filler * 4] * 3) + "\n\n"
        "---\n\n"
        "द्वितीय अध्याय स्पष्टाधिकार\n\n"
        "शीघ्रोच्च और मन्दोच्चफल की चर्चा स्पष्टाधिकार में की गयी है।\n",
        encoding="utf-8")
    monkeypatch.setenv("SS_BHASHYA_EN_PATH", str(en))
    monkeypatch.setenv("SS_BHASHYA_HI_PATH", str(hi))
    return en, hi


# --- offline: config ------------------------------------------------------------

def test_config_chapters_are_in_range_or_null():
    """Every chapter number in the config is 1-14 or null.

    Expected: no English range or Hindi boundary names a chapter outside the
    book's fourteen.
    """
    config = json.loads(bhashya.CONFIG_PATH.read_text(encoding="utf-8"))
    chapters = [r["chapter"] for r in config["en"]["chapters"]]
    chapters += [b["chapter"] for b in config["hi"]["boundaries"]]
    assert chapters
    assert all(c is None or 1 <= c <= 14 for c in chapters)


def test_config_english_ranges_ascend_without_overlap():
    """English page ranges are well formed, ascending and disjoint.

    Expected: each range has first_page <= last_page within 1-838, each
    starts after the previous one ends, and chapters 1-14 appear once each.
    """
    ranges = json.loads(
        bhashya.CONFIG_PATH.read_text(encoding="utf-8"))["en"]["chapters"]
    assert [r["chapter"] for r in ranges] == list(range(1, 15))
    previous_end = 0
    for r in ranges:
        assert 1 <= r["first_page"] <= r["last_page"] <= 838
        assert r["first_page"] > previous_end
        previous_end = r["last_page"]


def test_config_hindi_boundaries_cover_every_chapter_in_order():
    """Hindi anchors name chapters 1-14 once each, in order, with hints ascending.

    Expected: the non-null chapters read 1..14 and the line hints increase,
    so the in-order anchor search can find every one.
    """
    boundaries = json.loads(
        bhashya.CONFIG_PATH.read_text(encoding="utf-8"))["hi"]["boundaries"]
    assert [b["chapter"] for b in boundaries if b["chapter"]] == list(range(1, 15))
    hints = [b["line_hint"] for b in boundaries]
    assert hints == sorted(hints)
    assert all(b["anchor"] for b in boundaries)


def test_package_data_does_not_ship_the_commentary():
    """pyproject.toml's package-data bundles no commentary text.

    Expected: no package-data entry mentions the bhashya, a markdown file or
    the corpus package, since the commentary is copyrighted and local-only.
    """
    tomllib = pytest.importorskip("tomllib")
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"].get("package-data", {})
    entries = [e for files in package_data.values() for e in files]
    assert not [e for e in entries
                if "bhashya" in e.lower() or e.endswith(".md") or "corpus" in e]


# --- offline: missing files -------------------------------------------------------

def test_missing_files_mean_unavailable_and_empty_results(tmp_path, monkeypatch,
                                                          isolated_cache):
    """With both env paths pointing at files that do not exist, nothing raises.

    Expected: available() is False, search returns [] in both languages,
    get_page returns None, and backend() reports "none".
    """
    monkeypatch.setenv("SS_BHASHYA_EN_PATH", str(tmp_path / "absent_en.md"))
    monkeypatch.setenv("SS_BHASHYA_HI_PATH", str(tmp_path / "absent_hi.md"))
    assert bhashya.available() is False
    assert bhashya.search("mandocca") == []
    assert bhashya.search("मन्दोच्च") == []
    assert bhashya.get_page(24) is None
    assert bhashya.backend() == "none"


def test_unreachable_path_counts_as_missing(tmp_path, monkeypatch, isolated_cache):
    """A path that cannot be a file (its parent is a file) is treated as absent.

    Expected: available() returns False and search returns [] rather than
    either raising NotADirectoryError.
    """
    blocker = tmp_path / "not_a_directory"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("SS_BHASHYA_EN_PATH", str(blocker / "en.md"))
    monkeypatch.setenv("SS_BHASHYA_HI_PATH", str(blocker / "hi.md"))
    assert bhashya.available() is False
    assert bhashya.search("anything") == []


def test_only_one_source_present(synthetic_sources, tmp_path, monkeypatch):
    """With the Hindi file missing, English still searches and Hindi is empty.

    Expected: available() is True, backend() is "en" after a query, and a
    Devanagari query returns [] instead of failing.
    """
    monkeypatch.setenv("SS_BHASHYA_HI_PATH", str(tmp_path / "absent_hi.md"))
    assert bhashya.available() is True
    assert bhashya.search("mandocca")
    assert bhashya.backend() == "en"
    assert bhashya.search("मन्दोच्च") == []


# --- offline: synthetic sources ---------------------------------------------------

def test_synthetic_english_pages(synthetic_sources):
    """English chunking on a small file: one record per page, empty pages skipped.

    Expected: pages 1 and 24 are indexed with ids SB.en.p1 / SB.en.p24, page 2
    (a lone running header) is not; page 24 is Chapter 1 per the config and
    carries its ### heading and both verse marks; page 1 is front matter
    (chapter None) and its page-number heading "( 23)" is not used.
    """
    p1, p2, p24 = bhashya.get_page(1), bhashya.get_page(2), bhashya.get_page(24)
    assert p2 is None
    assert p1["id"] == "SB.en.p1" and p1["chapter"] is None
    assert p1["heading"] is None
    assert p24["id"] == "SB.en.p24"
    assert p24["chapter"] == 1
    assert p24["heading"] == "Chapter on Mean Motions"
    assert p24["verse_marks"] == [1, 2]
    assert p24["kind"] == "commentary" and p24["language"] == "en"
    assert p24["source"] == bhashya.SOURCE_EN


def test_synthetic_hindi_chunks(synthetic_sources):
    """Hindi chunking on a small file: sections split, figures dropped, windows bounded.

    Expected: a Devanagari query finds Chapter 1 text under its heading, with
    page None and the ॥२८॥ mark decoded to 28; no chunk contains the English
    figure description; every window is at most the window size; the plain
    body line anchor starts Chapter 2.
    """
    hits = bhashya.search("मन्दोच्च", chapter=1)
    assert hits
    first = hits[0]
    assert re.fullmatch(r"SB\.hi\.\d+", first["id"])
    assert first["language"] == "hi" and first["page"] is None
    assert first["heading"] == "मध्यमाधिकार"
    assert 28 in first["verse_marks"]
    assert first["source"] == bhashya.SOURCE_HI

    every = bhashya.search("परीक्षण", language="hi", limit=50)
    assert every
    assert all("Figure" not in h["text"] for h in every)
    assert all(len(h["text"]) <= bhashya._HINDI_WINDOW for h in every)
    assert {h["chapter"] for h in every} == {None, 1}

    chapter2 = bhashya.search("स्पष्टाधिकार", chapter=2)
    assert chapter2 and chapter2[0]["heading"] == "द्वितीय अध्याय स्पष्टाधिकार"


def test_synthetic_prefix_and_trigram_fallbacks(synthetic_sources):
    """Hindi words inside compounds are still found.

    Expected: "मन्दोच्चफल" is found exactly; "शीघ्र" (only present as the
    start of "शीघ्रोच्च") is found by the prefix tier; "च्चफ" (only inside a
    compound) is found by the trigram tier when SQLite supports it.
    """
    assert bhashya.search("मन्दोच्चफल")
    assert bhashya.search("शीघ्र")
    if "+trigram" in bhashya.backend():
        assert bhashya.search("च्चफ")


def test_language_auto_detection(synthetic_sources):
    """With language=None, Devanagari queries search Hindi and others English.

    Expected: a Latin query returns only "en" records, a Devanagari query
    only "hi" records, and an explicit language overrides the detection.
    """
    assert {h["language"] for h in bhashya.search("mandocca")} == {"en"}
    assert {h["language"] for h in bhashya.search("मन्दोच्च")} == {"hi"}
    assert bhashya.search("परीक्षण", language="en") == []


def test_queries_without_words_return_nothing(synthetic_sources):
    """Punctuation-only, danda-only and empty queries return [] without raising.

    Expected: FTS5 syntax characters and dandas are stripped, leaving no
    terms, and search short-circuits to [].
    """
    for query in ("", '"*()', "॥", "।।", "   "):
        assert bhashya.search(query) == []
    assert bhashya.search("mandocca", limit=0) == []


def test_cache_rebuilds_when_source_changes(synthetic_sources, isolated_cache):
    """Editing a source file builds a new cache and removes the old one.

    Expected: after appending a page with a new word, the word is found, and
    only one cache file for these sources remains in the cache directory.
    """
    en, _ = synthetic_sources
    assert bhashya.search("zygomorphic") == []
    with en.open("a", encoding="utf-8") as handle:
        handle.write("\n## Source page 25\n\nA zygomorphic word appears on "
                      "this page, which is long enough to be indexed here.\n")
    stat = en.stat()
    os.utime(en, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
    assert [h["id"] for h in bhashya.search("zygomorphic")] == ["SB.en.p25"]
    assert len(list(isolated_cache.glob("surya_bhashya_*.db"))) == 1


# --- live sources -----------------------------------------------------------------

@live
def test_english_page_split():
    """The translation splits into one chunk per non-empty scanned page.

    Expected: between 820 and 838 English chunks (838 pages less a handful of
    blank scans), every id of the form SB.en.p<N> matching its page, and
    page 24 (the start of Chapter 1) present.
    """
    con = bhashya._connect()
    try:
        rows = con.execute(
            "SELECT id, page FROM chunks WHERE language='en'").fetchall()
    finally:
        con.close()
    assert 820 <= len(rows) <= 838
    assert all(r["id"] == f"SB.en.p{r['page']}" for r in rows)
    assert bhashya.get_page(24)["chapter"] == 1


@live
def test_english_term_returns_cited_hits():
    """A known English term returns commentary hits with source, page and snippet.

    Expected: "precession" returns hits, each kind "commentary", language
    "en", carrying the English source string, an integer page and a snippet
    with the match marked; the top hit is in Chapter 3, where the
    commentary discusses ayana-calana.
    """
    hits = bhashya.search("precession")
    assert hits
    for hit in hits:
        assert hit["kind"] == "commentary"
        assert hit["language"] == "en"
        assert hit["source"] == bhashya.SOURCE_EN
        assert isinstance(hit["page"], int)
        assert "<<" in hit["snippet"]
    assert hits[0]["chapter"] == 3


@live
def test_devanagari_term_returns_hindi_hits():
    """A Devanagari term (मन्दोच्च) returns Hindi OCR hits.

    Expected: hits with ids SB.hi.<n>, language "hi", page None, the Hindi
    source string, and the term marked in the snippet.
    """
    hits = bhashya.search("मन्दोच्च")
    assert hits
    for hit in hits:
        assert re.fullmatch(r"SB\.hi\.\d+", hit["id"])
        assert hit["language"] == "hi" and hit["page"] is None
        assert hit["source"] == bhashya.SOURCE_HI
    assert any("<<मन्दोच्च>>" in hit["snippet"] for hit in hits)


@live
def test_chapter_filter():
    """The chapter filter restricts hits to the requested chapter in both languages.

    Expected: "eclipse" in Chapter 4 and "मन्दोच्च" in Chapter 2 return only
    hits from those chapters; a filter on a chapter the term never occurs in
    can return [] but never hits from elsewhere.
    """
    english = bhashya.search("eclipse", chapter=4, limit=10)
    hindi = bhashya.search("मन्दोच्च", chapter=2, limit=10)
    assert english and {h["chapter"] for h in english} == {4}
    assert hindi and {h["chapter"] for h in hindi} == {2}
    assert all(h["chapter"] == 12 for h in bhashya.search("मन्दोच्च", chapter=12))


@live
def test_every_chapter_has_chunks_in_both_languages():
    """Each of the 14 chapters gets chunks from both sources.

    Expected: a non-zero count for every (language, chapter) pair, so no
    chapter boundary in the config was silently missed.
    """
    con = bhashya._connect()
    try:
        counts = {(r[0], r[1]): r[2] for r in con.execute(
            "SELECT language, chapter, COUNT(*) FROM chunks "
            "WHERE chapter IS NOT NULL GROUP BY language, chapter")}
    finally:
        con.close()
    for language in ("en", "hi"):
        for chapter in range(1, 15):
            assert counts.get((language, chapter), 0) > 0, (language, chapter)


@live
def test_hindi_anchors_resolve_at_their_line_hints():
    """Every Hindi anchor in the config is found, in order, on its hinted line.

    Expected: scanning the OCR with the module's own line cleaning, each
    anchor's first match after the previous anchor is exactly line_hint, so
    the hand-checked boundaries still hold for the current OCR file.
    """
    lines = bhashya._hi_path().read_text(encoding="utf-8").splitlines()
    boundaries = json.loads(
        bhashya.CONFIG_PATH.read_text(encoding="utf-8"))["hi"]["boundaries"]
    i = 0
    for boundary in boundaries:
        while i < len(lines) and bhashya._clean_line(lines[i]).strip() != boundary["anchor"]:
            i += 1
        assert i + 1 == boundary["line_hint"], boundary
        i += 1


@live
def test_available_and_backend_with_live_sources():
    """With both files present the module reports both sources.

    Expected: available() is True and, after a query, backend() starts with
    "en+hi".
    """
    assert bhashya.available() is True
    bhashya.search("eclipse", limit=1)
    assert bhashya.backend().startswith("en+hi")
