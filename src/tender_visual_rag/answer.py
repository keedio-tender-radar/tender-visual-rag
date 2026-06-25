"""Síntesis de respuesta con LLM (OpenRouter), fundamentada en los fragmentos recuperados.

Si no hay `OPENROUTER_API_KEY`, el llamante usa la respuesta extractiva (top fragmento). El
cliente httpx es monkeypatcheable en tests.
"""

from __future__ import annotations

import httpx

from tender_visual_rag.config import settings

_SYSTEM = (
    "Eres un analista de licitaciones públicas. Responde la pregunta usando SOLO el contexto "
    "del pliego. Sé conciso y concreto (criterios, solvencia, plazos, importes). Si el contexto "
    "no contiene la respuesta, dilo claramente."
)


def _client() -> httpx.Client:
    return httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        timeout=60,
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
    )


def synthesize(question: str, contexts: list[str]) -> str | None:
    """Devuelve una respuesta generada a partir del contexto, o None si no hay clave/contexto."""
    if not settings.openrouter_api_key or not contexts:
        return None
    context = "\n\n---\n\n".join(contexts)[:8000]
    user = f"Contexto del pliego:\n{context}\n\nPregunta: {question}"
    with _client() as client:
        resp = client.post(
            "/chat/completions",
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
