"""Tests for the /glossary routes that feed the React glossary panel."""
import pytest
from fastapi.testclient import TestClient

from suryasiddhanta.api.glossary import IMAGE_DIR
from suryasiddhanta.api.main import app

client = TestClient(app)


def test_glossary_returns_document_with_cache_headers():
    """GET /glossary returns the whole document with a strong ETag and a
    public max-age, so the browser can revalidate instead of re-downloading."""
    r = client.get("/glossary")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == 1
    assert body["terms"] and isinstance(body["routes"], dict)
    assert r.headers["etag"].startswith('"') and r.headers["etag"].endswith('"')
    assert "max-age=3600" in r.headers["cache-control"]


def test_glossary_revalidates_with_304():
    """A request carrying the current ETag gets 304 with no body."""
    etag = client.get("/glossary").headers["etag"]
    r = client.get("/glossary", headers={"If-None-Match": etag})
    assert r.status_code == 304
    assert r.content == b""


def test_glossary_stale_etag_gets_full_body():
    """A stale ETag is ignored and the full document is returned."""
    r = client.get("/glossary", headers={"If-None-Match": '"stale"'})
    assert r.status_code == 200


def test_image_served_as_svg():
    """A shipped diagram is served as image/svg+xml with nosniff and a
    CSP that stops any script inside it from running when opened directly."""
    name = sorted(p.name for p in IMAGE_DIR.glob("*.svg"))[0]
    r = client.get(f"/glossary/img/{name}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in r.headers["content-security-policy"]


@pytest.mark.parametrize(
    "name", ["missing.svg", "Upper.svg", "note.png", "..glossary.json", "..%2Fglossary.json"]
)
def test_image_rejects_bad_names(name):
    """Unknown, wrongly cased, non-SVG and traversal-shaped names all 404."""
    assert client.get(f"/glossary/img/{name}").status_code == 404
