"""Interfaz del backend de RAG visual.

Permite cambiar entre el motor real (PixelRAG + Qwen3-VL) y un doble determinista para
dev/tests. La indización y la consulta son SIEMPRE por `tender_id` (ADR 004: RAG por expediente).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Hit:
    tender_id: str
    page: int
    score: float
    ref: str | None = None


class VisualRagBackend(ABC):
    name: str = "base"

    @abstractmethod
    def index(self, tender_id: str, documents: list[dict]) -> int:
        """Indiza los documentos del expediente. Devuelve el nº de páginas indizadas."""

    @abstractmethod
    def query(self, tender_id: str, text: str, n_docs: int) -> list[Hit]:
        """Devuelve las páginas más relevantes del expediente para la consulta."""
