# Imagen del servicio. El motor real PixelRAG (Qwen3-VL) es pesado: descomenta su instalación
# y usa una máquina con memoria suficiente (idealmente GPU). Por defecto arranca con backend="fake".
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Para el backend real: poppler (render PDF) y pixelrag.
# RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir \
      "fastapi>=0.115" "uvicorn[standard]>=0.32" "httpx>=0.27" "pydantic>=2.6" "pydantic-settings>=2.5"
# Backend real (descomenta y dimensiona la máquina):
# RUN pip install --no-cache-dir 'pixelrag[embed,index,serve,pdf]'

COPY . .

EXPOSE 8000

CMD ["uvicorn", "tender_visual_rag.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
