"""Backend real basado en PixelRAG (Qwen3-VL).

Orquesta el CLI de PixelRAG por subproceso para render+embed+index, y consulta un
`pixelrag serve` por HTTP (`POST /search`). Pensado para correr en una máquina con el modelo
`Qwen3-VL-Embedding-2B` y poppler instalados (no cabe en una máquina pequeña).

Requisitos del entorno de despliegue:
    pip install 'pixelrag[embed,index,serve,pdf]'
    pixelrag serve --index-dir <data>/index/<tender_id> --port 30001
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import httpx

from tender_visual_rag.backends.base import Hit, VisualRagBackend
from tender_visual_rag.config import settings


class PixelRagError(RuntimeError):
    pass


def _run(cmd: list[str]) -> None:
    if shutil.which(cmd[0]) is None:
        raise PixelRagError(f"'{cmd[0]}' no está en PATH. Instala pixelrag en el entorno.")
    proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if proc.returncode != 0:
        raise PixelRagError(f"{' '.join(cmd)} falló: {proc.stderr[:300]}")


class PixelRagBackend(VisualRagBackend):
    name = "pixelrag"

    def __init__(self) -> None:
        self.root = Path(settings.data_dir)

    def _tiles_dir(self, tender_id: str) -> Path:
        return self.root / "tiles" / tender_id

    def _index_dir(self, tender_id: str) -> Path:
        return self.root / "index" / tender_id

    def index(self, tender_id: str, documents: list[dict]) -> int:
        tiles = self._tiles_dir(tender_id)
        tiles.mkdir(parents=True, exist_ok=True)
        sources = [
            d.get("path") or d.get("url") for d in documents if d.get("path") or d.get("url")
        ]
        if not sources:
            raise PixelRagError("El backend real requiere documentos con 'url' o 'path'.")

        for src in sources:
            _run(["pixelshot", src, "-o", str(tiles), "--dpi", str(settings.render_dpi)])

        emb = self.root / "embeddings" / tender_id
        index = self._index_dir(tender_id)
        _run(["pixelrag", "chunk", "--tiles-dir", str(tiles)])
        embed_cmd = ["pixelrag", "embed", "--shard-dir", str(tiles), "--output-dir", str(emb)]
        if settings.pixelrag_gpu_ids:
            embed_cmd += ["--gpu-ids", settings.pixelrag_gpu_ids]
        _run(embed_cmd)
        _run(["pixelrag", "build-index", "--embeddings-dir", str(emb), "--output-dir", str(index)])

        return sum(1 for _ in tiles.glob("**/*.png"))

    def query(self, tender_id: str, text: str, n_docs: int) -> list[Hit]:
        try:
            with httpx.Client(base_url=settings.pixelrag_serve_url, timeout=60) as client:
                resp = client.post(
                    "/search", json={"queries": [{"text": text}], "n_docs": n_docs}
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise PixelRagError(f"pixelrag serve no respondió: {exc}") from exc

        return _parse_hits(tender_id, data)


def _parse_hits(tender_id: str, data: dict) -> list[Hit]:
    """Mapea la respuesta de /search a Hits, de forma tolerante al esquema exacto."""
    results = data.get("results") or data.get("hits") or []
    if results and isinstance(results[0], list):
        results = results[0]  # /search devuelve una lista por query
    hits: list[Hit] = []
    for i, r in enumerate(results):
        hits.append(
            Hit(
                tender_id=tender_id,
                page=int(r.get("page", r.get("doc_id", i)) or i),
                score=float(r.get("score", 0.0) or 0.0),
                ref=r.get("image", r.get("ref")),
            )
        )
    return hits
