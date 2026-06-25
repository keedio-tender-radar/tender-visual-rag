"""Backend determinista en memoria (dev/tests).

Simula el RAG visual sin modelo: trocea el texto de cada documento en "páginas" y puntúa por
solape de palabras con la consulta. Útil para validar el servicio y la API sin Qwen3-VL.
"""

from __future__ import annotations

import re

from tender_visual_rag.backends.base import Hit, VisualRagBackend


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2}


def _pages_from_doc(doc: dict) -> list[str]:
    text = doc.get("text") or doc.get("url") or doc.get("path") or doc.get("filename") or ""
    paragraphs = [p.strip() for p in str(text).split("\n") if p.strip()]
    return paragraphs or [str(text)]


class FakeBackend(VisualRagBackend):
    name = "fake"

    def __init__(self) -> None:
        # tender_id -> list[(ref, text)]
        self._store: dict[str, list[tuple[str, str]]] = {}

    def index(self, tender_id: str, documents: list[dict]) -> int:
        pages = self._store.setdefault(tender_id, [])
        for di, doc in enumerate(documents):
            for pi, page_text in enumerate(_pages_from_doc(doc)):
                ref = f"{tender_id}/doc{di}/page{pi}"
                pages.append((ref, page_text))
        return len(pages)

    def query(self, tender_id: str, text: str, n_docs: int) -> list[Hit]:
        pages = self._store.get(tender_id, [])
        qwords = _words(text)
        scored = []
        for page_no, (ref, page_text) in enumerate(pages):
            overlap = len(qwords & _words(page_text))
            if overlap:
                score = overlap / (len(qwords) or 1)
                scored.append(Hit(tender_id=tender_id, page=page_no, score=score, ref=ref))
        scored.sort(key=lambda h: (-h.score, h.page))
        return scored[:n_docs]
