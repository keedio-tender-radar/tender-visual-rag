# tender-visual-rag

> 🖼️ RAG **visual** (PixelRAG / Qwen3-VL) por expediente para **Keedio Tender Radar**. Recupera
> las **páginas de los pliegos como imagen** —tablas de criterios, baremos de solvencia, anexos
> con layout— que la extracción de texto pierde. Objetivo: **más precisión** en criterios,
> solvencia y chat documental.

Complementa a `tender-document-service` (texto): el texto sirve para keywords/estructura; aquí se
añade el canal visual. Indexación y consulta **siempre por `tender_id`** (ADR 004: RAG por
expediente).

## Por qué PixelRAG

[PixelRAG](https://github.com/StarTrail-org/PixelRAG) (Apache-2.0) renderiza páginas a imagen y
las recupera con un modelo fine-tuneado `Qwen3-VL-Embedding-2B` + FAISS, en vez de parsear a
texto. La API hosted sirve un índice de Wikipedia, así que para **nuestros pliegos** se usa el
modo **self-hosted** (render → embed → index → serve).

## Arquitectura

```
POST /index {tender_id, documents}      →  backend.index()  →  tiles + índice FAISS por tender_id
POST /query {tender_id, text, n_docs}   →  backend.query()  →  páginas-imagen más relevantes
```

- **Backend** intercambiable (`backends/`):
  - `fake` (por defecto, dev/tests): determinista, en memoria, sin modelo.
  - `pixelrag` (real): orquesta `pixelshot` + `pixelrag` (chunk/embed/build-index) por subproceso y
    consulta `pixelrag serve` (`POST /search`).
- Las páginas recuperadas alimentan al modelo multimodal de `tender-ai-analysis-service` / chat.

## Requisitos del backend real

- `pip install 'pixelrag[embed,index,serve,pdf]'`, **poppler** (render PDF), y el modelo
  `Qwen3-VL-Embedding-2B`.
- **Infra**: el modelo (~2B) **no cabe en máquinas pequeñas** (512 MB). Requiere una máquina con
  memoria suficiente (idealmente GPU). Por eso la imagen arranca con `backend=fake` y el real se
  habilita por configuración + máquina dimensionada.

## Ejecutar

```bash
python -m venv .venv && . .venv/Scripts/activate    # Linux/mac: source .venv/bin/activate
pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings pytest ruff
uvicorn tender_visual_rag.main:app --app-dir src --reload   # backend=fake por defecto
pytest -q          # 11 tests (fake backend + API + parser de pixelrag serve)
ruff check src tests
```

Activar el backend real: `BACKEND=pixelrag`, instalar pixelrag+poppler+modelo y levantar
`pixelrag serve --index-dir <data>/index/<tender_id> --port 30001`.

## Integración en la plataforma

1. `tender-document-service` descarga el pliego (PDF).
2. `tender-visual-rag` lo indexa por `tender_id` (render→embed→index).
3. En análisis/chat, una consulta (p. ej. "criterios de adjudicación") devuelve las páginas
   relevantes; un LLM multimodal las lee → respuestas con cita visual y mejor precisión.
