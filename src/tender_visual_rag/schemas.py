from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentRef(BaseModel):
    """Documento a indizar: URL o ruta local, más un texto opcional (para dev/tests)."""

    url: str | None = None
    path: str | None = None
    text: str | None = None
    filename: str | None = None


class IndexRequest(BaseModel):
    tender_id: str
    documents: list[DocumentRef] = Field(default_factory=list)


class IndexResponse(BaseModel):
    tender_id: str
    indexed_pages: int
    backend: str


class QueryRequest(BaseModel):
    tender_id: str
    text: str
    n_docs: int | None = None


class Hit(BaseModel):
    tender_id: str
    page: int
    score: float
    ref: str | None = None  # ruta/clave de la imagen de la página


class QueryResponse(BaseModel):
    tender_id: str
    query: str
    hits: list[Hit] = Field(default_factory=list)
    backend: str
