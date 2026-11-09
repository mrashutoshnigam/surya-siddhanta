"""Tests for query expansion in corpus/retrieve.py.

The synonym tables come from the packaged glossary plus a few hand-added
groups, so these run offline; only the last test searches the corpus.
"""
from suryasiddhanta.corpus import retrieve


def test_fold_drops_diacritics_and_case():
    """
    Transliteration variants compare equal after folding.
    Expected: "Ayanāṃśa" folds to "ayanamsa".
    """
    assert retrieve._fold("Ayanāṃśa") == "ayanamsa"


def test_glossary_aliases_are_two_way():
    """
    A glossary term and its English alias expand to each other.
    Expected: lagna -> ascendant and ascendant -> lagna.
    """
    assert "ascendant" in retrieve._synonyms_of("lagna")
    assert "lagna" in retrieve._synonyms_of("ascendant")


def test_hand_added_groups_cover_terms_missing_from_glossary():
    """
    Terms the glossary lacks still expand via _EXTRA_SYNONYMS.
    Expected: jya -> sine, mandocca -> apogee.
    """
    assert "sine" in retrieve._synonyms_of("jya")
    assert "apogee" in retrieve._synonyms_of("mandocca")


def test_expansion_matches_whole_words_only():
    """
    A synonym key inside a longer word does not trigger expansion.
    Expected: "cosine" yields no jya-group synonyms.
    """
    assert "jya" not in retrieve._expansions("cosine rule")


def test_expansion_matches_phrases_and_skips_query_terms():
    """
    Multi-word glossary aliases are recognised in a query, and the query's
    own words are not repeated as expansions.
    Expected: "precession of the equinoxes" expands to ayanamsha, not "precession".
    """
    out = retrieve._expansions("what is the precession of the equinoxes")
    assert "ayanamsha" in out
    assert "precession" not in out


def test_expansion_is_capped():
    """
    A long question cannot balloon the FTS5 MATCH expression.
    Expected: at most `cap` expansions.
    """
    q = "lagna jya mandocca tithi ghati nakshatra lambana nati valana ahargana"
    assert len(retrieve._expansions(q, cap=5)) <= 5


def test_search_finds_verses_through_a_synonym():
    """
    A query word the translation never uses still reaches the verses that
    use its synonym (Burgess says "sine"; the user says "jya").
    Expected: "jya table" returns Chapter 2 sine-table verses.
    """
    hits = retrieve.search("jya table", limit=5)
    assert any(h["chapter"] == 2 for h in hits)
