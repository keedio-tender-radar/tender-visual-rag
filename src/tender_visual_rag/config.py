"""Configuración del servicio de RAG visual (PixelRAG)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "tender-visual-rag"
    version: str = "0.1.0"

    # Backend: "pixelrag" (real, requiere modelo+poppler) o "fake" (dev/tests).
    backend: str = "fake"

    # Datos locales: tiles e índices por expediente.
    data_dir: str = "./data"
    render_dpi: int = 200
    default_n_docs: int = 5

    # PixelRAG real.
    pixelrag_serve_url: str = "http://localhost:30001"  # `pixelrag serve` para /search
    pixelrag_model: str = "Qwen3-VL-Embedding-2B"
    pixelrag_gpu_ids: str = ""  # vacío = CPU

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
