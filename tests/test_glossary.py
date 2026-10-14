"""Integrity checks for data/glossary.json.

These guard the things the UI cannot recover from gracefully: dangling
links, ambiguous aliases, missing diagrams and citations that do not exist
in the corpus.
"""
import re

import pytest

from suryasiddhanta.api.glossary import IMAGE_DIR, load_glossary

#: Every React route; keep in step with frontend/src/App.tsx.
KNOWN_ROUTES = [
    "/positions", "/panchanga", "/eclipse/lunar", "/eclipse/solar",
    "/conjunctions", "/stars", "/heliacal", "/moon", "/patas",
    "/cosmography", "/instruments", "/place-time", "/daily-panchanga",
    "/chat", "/book/1",
]
#: The categories the panel knows how to group and label.
CATEGORIES = {
    "concept", "unit", "place", "planet", "rashi", "nakshatra", "tithi",
    "yoga", "karana", "weekday", "month", "season", "samvatsara", "instrument",
    "star",
}
_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_CITE = re.compile(r"SS\.(\d+)\.(\d+)")

DOC = load_glossary()
TERMS = DOC["terms"]


def test_every_term_has_required_fields_with_right_types():
    """Each term has a kebab-case id, a display name, a known category, a
    short definition of at most 140 characters and at least one full
    paragraph, all as plain strings with no markup."""
    for tid, t in TERMS.items():
        assert _ID.fullmatch(tid), tid
        assert isinstance(t["term"], str) and t["term"], tid
        assert t["category"] in CATEGORIES, tid
        assert isinstance(t["short"], str) and 0 < len(t["short"]) <= 140, tid
        assert t["full"] and all(isinstance(p, str) and p for p in t["full"]), tid
        assert "<" not in " ".join(t["full"]) + t["short"], f"markup in {tid}"


def test_no_name_or_alias_is_shared_between_terms():
    """A name maps to exactly one term, case-folded and whitespace-collapsed,
    so the page scan never has to guess which entry a word means."""
    owner = {}
    for tid, t in TERMS.items():
        for name in [t["term"], *t.get("aliases", [])]:
            key = " ".join(name.split()).casefold()
            assert owner.setdefault(key, tid) == tid, f"{name!r}: {owner[key]} and {tid}"


def test_related_ids_exist_and_are_not_self():
    """Every related link opens a real term other than the one it is on."""
    for tid, t in TERMS.items():
        for rid in t.get("related", []):
            assert rid in TERMS and rid != tid, f"{tid} -> {rid}"


def test_route_lists_use_known_routes_and_terms():
    """Route keys are real routes, every listed id exists, and no route
    lists a term twice."""
    for route, ids in DOC["routes"].items():
        assert route in KNOWN_ROUTES, route
        assert len(ids) == len(set(ids)), route
        for tid in ids:
            assert tid in TERMS, f"{route}: {tid}"


def test_match_routes_are_known():
    """A term restricted to certain routes is restricted to routes that
    exist, and the list is not empty (use null for 'any route')."""
    for tid, t in TERMS.items():
        routes = (t.get("match") or {}).get("routes")
        if routes is not None:
            assert routes and set(routes) <= set(KNOWN_ROUTES), tid


def test_images_exist_and_have_alt_text():
    """Every referenced diagram ships in glossary_img and carries alt text."""
    for tid, t in TERMS.items():
        image = t.get("image")
        if image:
            assert (IMAGE_DIR / image["src"]).is_file(), tid
            assert image["alt"].strip(), tid


def test_every_shipped_image_is_used():
    """No orphan diagrams: each SVG in glossary_img belongs to some term."""
    used = {t["image"]["src"] for t in TERMS.values() if t.get("image")}
    shipped = {p.name for p in IMAGE_DIR.glob("*.svg")}
    assert shipped <= used, shipped - used


def test_equations_are_non_empty_latex():
    """Each equation carries LaTeX source."""
    for tid, t in TERMS.items():
        for eq in t.get("equations", []):
            assert eq["latex"].strip(), tid


def test_citations_resolve_in_corpus():
    """Every SS.c.v citation names a verse the corpus actually holds.
    Skipped when no corpus is reachable, so the suite stays offline-safe."""
    retrieve = pytest.importorskip("suryasiddhanta.corpus.retrieve")
    try:
        retrieve.get_verse(1, 1)
    except Exception as exc:  # noqa: BLE001 - any corpus failure means "not available"
        pytest.skip(f"corpus unavailable: {exc}")
    for tid, t in TERMS.items():
        for cite in t.get("cite", []):
            m = _CITE.fullmatch(cite)
            assert m, f"{tid}: {cite}"
            assert retrieve.get_verse(int(m[1]), int(m[2])), f"{tid}: {cite}"


def test_every_route_has_a_core_list():
    """Every page opens with a curated list of its terms, even before a
    calculation has run or the page scan has found anything."""
    for route in KNOWN_ROUTES:
        assert DOC["routes"].get(route), route
