"""tender-visual-rag — RAG visual (PixelRAG) por expediente para Keedio Tender Radar."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from tender_visual_rag.config import settings
from tender_visual_rag.schemas import (
    Hit,
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
)
from tender_visual_rag.service import get_backend

app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "backend": get_backend().name,
    }


@app.post("/index", response_model=IndexResponse)
def index(payload: IndexRequest) -> IndexResponse:
    if not payload.documents:
        raise HTTPException(422, "Indica al menos un documento.")
    backend = get_backend()
    try:
        pages = backend.index(payload.tender_id, [d.model_dump() for d in payload.documents])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Indexación fallida: {exc}") from exc
    return IndexResponse(tender_id=payload.tender_id, indexed_pages=pages, backend=backend.name)


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    backend = get_backend()
    n = payload.n_docs or settings.default_n_docs
    try:
        hits = backend.query(payload.tender_id, payload.text, n)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Consulta fallida: {exc}") from exc
    return QueryResponse(
        tender_id=payload.tender_id,
        query=payload.text,
        hits=[Hit(tender_id=h.tender_id, page=h.page, score=h.score, ref=h.ref) for h in hits],
        backend=backend.name,
    )
