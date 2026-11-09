"""Server-owned scene context and a closed set of user-activated tours."""
from .explorer_catalog import BODIES
from .explorer_core import snapshot
from .explorer_schemas import ExplorerContextIn, parse_instant

DEMONSTRATIONS = {
    "spin": "A spin and a journey", "moon": "Follow the Moon",
    "retrograde": "Mars moves backward", "models": "Two ways to see",
}


def scene_context(request: ExplorerContextIn):
    info = BODIES.get(request.body)
    if info is None or request.model not in info.models:
        raise ValueError("Choose a body supported by the selected explorer model")
    data = snapshot(request.model, parse_instant(request.instant).timestamp())
    # Exact trusted facts for the selected body plus Earth/Sun for context.
    data["bodies"] = {key: value for key, value in data["bodies"].items() if key in {request.body, "Earth", "Sun"}}
    return dict(body=request.body, beginner=request.beginner, snapshot=data,
        facts=info.model_dump(),
        illustration="Screen radii, globe sizes, surface orientation and spin speed are adjusted for visibility. Historical Earth has a fixed position, but its surface spin is a modern illustration.")


def scene_sources(context):
    return [dict(id="explorer:"+source.url, kind="reference", label=source.label, url=source.url,
        chapter=None, verse=None, page=None, snippet="Curated source for the explorer’s body facts or historical model.")
        for source in BODIES[context["body"]].sources
        if context["snapshot"]["model"] == "historical" or not source.url.startswith("/")]


def demonstrations(message):
    """Only server-defined tours; neither model output nor client code is run."""
    text = message.casefold()
    ids = []
    if any(word in text for word in ("retrograde", "backward", "backwards")):
        ids.append("retrograde")
    if any(word in text for word in ("moon", "lunar", "chandra")):
        ids.append("moon")
    if any(word in text for word in ("spin", "rotation", "rotate", "axis")):
        ids.append("spin")
    if any(word in text for word in ("compare", "difference", "geocentric", "heliocentric", "model")):
        ids.append("models")
    return [dict(id=id, label=DEMONSTRATIONS[id]) for id in ids]
