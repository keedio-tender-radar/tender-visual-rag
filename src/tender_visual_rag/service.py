"""Selección y ciclo de vida del backend de RAG visual."""

from __future__ import annotations

from tender_visual_rag.backends.base import VisualRagBackend
from tender_visual_rag.config import settings

_backend: VisualRagBackend | None = None


def _build() -> VisualRagBackend:
    if settings.backend == "pixelrag":
        from tender_visual_rag.backends.pixelrag_backend import PixelRagBackend

        return PixelRagBackend()
    from tender_visual_rag.backends.fake_backend import FakeBackend

    return FakeBackend()


def get_backend() -> VisualRagBackend:
    global _backend
    if _backend is None:
        _backend = _build()
    return _backend


def reset_backend() -> None:
    """Reinicia el backend (útil en tests para estado limpio)."""
    global _backend
    _backend = None
