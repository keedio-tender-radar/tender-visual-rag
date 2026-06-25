"""tender-visual-rag — RAG visual (PixelRAG) por expediente para Keedio Tender Radar."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from tender_visual_rag.config import settings
from tender_visual_rag.schemas import (
    AskRequest,
    AskResponse,
    AskSource,
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


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    """Pregunta por expediente (contrato de la plataforma).

    Si llega `document_text`, indiza al vuelo (permite responder sin pre-ingesta); luego recupera
    las páginas más relevantes y compone una respuesta extractiva. Con el backend real
    (PixelRAG/Qwen3-VL) la recuperación es visual y la respuesta la genera el VLM.
    """
    backend = get_backend()
    try:
        if payload.document_text:
            backend.index(payload.tender_id, [{"text": payload.document_text}])
        hits = backend.query(payload.tender_id, payload.question, payload.top_k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Consulta fallida: {exc}") from exc
    answer = hits[0].content[:800] if hits and hits[0].content else None
    return AskResponse(
        tender_id=payload.tender_id,
        question=payload.question,
        answer=answer,
        sources=[
            AskSource(page=h.page, ref=h.ref, content=(h.content or "")[:600]) for h in hits
        ],
        backend=backend.name,
    )
