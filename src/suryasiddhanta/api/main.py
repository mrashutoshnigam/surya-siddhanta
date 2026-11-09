"""FastAPI app entry point.

Run:
    uvicorn suryasiddhanta.api.main:app --reload
"""
from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI

from . import book, book_ch02, book_ch03, book_ch04, book_ch05, book_ch06, book_ch07, book_ch08, book_ch09, book_ch10, book_ch11, book_ch12, book_ch13, book_ch14, calc, chat, corpus, glossary

app = FastAPI(title="Surya Siddhanta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# The glossary document is ~100 KB of JSON; gzip cuts it to about a quarter.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(calc.router)
app.include_router(chat.router)
app.include_router(corpus.router)
app.include_router(book.router)
app.include_router(book_ch02.router)
app.include_router(book_ch03.router)
app.include_router(book_ch04.router)
app.include_router(book_ch05.router)
app.include_router(book_ch06.router)
app.include_router(book_ch07.router)
app.include_router(book_ch08.router)
app.include_router(book_ch09.router)
app.include_router(book_ch10.router)
app.include_router(book_ch11.router)
app.include_router(book_ch12.router)
app.include_router(book_ch13.router)
app.include_router(book_ch14.router)
app.include_router(glossary.router)


@app.get("/")
def root():
    """Service index for the bare backend URL.

    The API only mounts ``/api/*`` routes plus ``/docs``; it has no HTML UI of
    its own (the React frontend at :5173 proxies ``/api`` here). Hitting
    ``http://127.0.0.1:8000/`` directly therefore used to 404, which read like a
    crash. This returns a small discovery payload pointing at the real surfaces.
    """
    return {
        "service": "Surya Siddhanta API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "frontend": "http://localhost:5173",
        "note": "REST routes live under /api/* and /book/*; the web UI is the React app on :5173.",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
