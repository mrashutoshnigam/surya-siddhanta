# Surya Siddhanta

A Python implementation of the astronomical algorithms of the *Surya Siddhanta*
(Burgess 1860 translation), all fourteen chapters, with a React web interface and
the code that regenerates the paper *Surya Siddhanta vs. DE440*.

The historical calculation library uses the text's own formulas (`numpy` is its
only runtime dependency). The Universe Explorer also offers an independent modern
view using Skyfield and verified JPL DE440 data.

## Layout

| Path | Contents |
|---|---|
| `src/suryasiddhanta/ch01_*.py` … `ch14_*.py` | One module per chapter of the text |
| `src/suryasiddhanta/planets/` | The same functions grouped by graha |
| `src/suryasiddhanta/api/` | FastAPI backend for the web interface |
| `src/suryasiddhanta/chatbot/`, `corpus/` | Tool layer and verse retrieval used by the API |
| `frontend/` | React + TypeScript interface |
| `docs/evaluation/` | Paper, regeneration script and published results |
| `tests/` | Test suite |

## Library

```bash
pip install surya-siddhanta
```

```python
from suryasiddhanta.ch02_true_places import compute

print(compute("Mars", 2024, 1, 1).true_longitude)   # sidereal degrees
```

Julian Days are reckoned in Ujjain mean time and longitudes are sidereal, as in the text.

## Web interface

```bash
pip install -e ".[api,astronomy]"
python docker/fetch_ephemeris.py                 # verified DE440 for the modern view
uvicorn suryasiddhanta.api.main:app --reload    # backend on :8000
cd frontend && npm ci && npm run dev             # frontend on :5173
```

Open `/universe` for the planet explorer. See [the explorer guide](docs/universe-explorer.md)
for its controls, historical and modern models, and verification commands.

Chat needs `OPENROUTER_API_KEY` or `DEEPSEEK_API_KEY`. Verse lookup uses the bundled
`src/suryasiddhanta/corpus/data/corpus.json`; `SS_CORPUS_JSON_PATH` /
`SS_CORPUS_DB_PATH` optionally select an external corpus.

Build and run the combined React/FastAPI Docker image with:

```bash
docker compose -f docker-compose.ui.yml up --build
```

The image includes the corpus, verified DE440 kernel, planet textures, logo and
project PDFs. The footer's “About this project” button opens the introduction on
every page; the introduction opens automatically on the first home-page visit.

## Reproducing the paper

See [docs/evaluation/REPRODUCE.md](docs/evaluation/REPRODUCE.md). In short:

```bash
pip install -e ".[plot,dev]" jplephem
# download de440.bsp from JPL NAIF into paper/data/kernels/
python docs/evaluation/regenerate_paper.py
```

## Tests

```bash
pip install -e ".[dev,api]"
pytest
```

The corpus tests need the verse corpus file described above.

## License

MIT, see [LICENSE](LICENSE).
