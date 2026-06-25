from fastapi.testclient import TestClient

from tender_visual_rag.main import app

client = TestClient(app)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["backend"] == "fake"


def test_index_and_query_flow():
    idx = client.post(
        "/index",
        json={
            "tender_id": "T1",
            "documents": [
                {"text": "Criterios de adjudicación y solvencia técnica del pliego."},
                {"text": "Objeto: plataforma de datos."},
            ],
        },
    )
    assert idx.status_code == 200
    assert idx.json()["indexed_pages"] == 2

    q = client.post("/query", json={"tender_id": "T1", "text": "solvencia técnica", "n_docs": 3})
    assert q.status_code == 200
    body = q.json()
    assert body["backend"] == "fake"
    assert body["hits"]
    assert body["hits"][0]["tender_id"] == "T1"


def test_index_requires_documents():
    assert client.post("/index", json={"tender_id": "T1", "documents": []}).status_code == 422


def test_query_unknown_tender_returns_empty():
    body = client.post("/query", json={"tender_id": "nope", "text": "x"}).json()
    assert body["hits"] == []


def test_ask_with_document_text():
    r = client.post(
        "/ask",
        json={
            "question": "solvencia tecnica",
            "tender_id": "EXP-9",
            "document_text": "Objeto del contrato.\nSe exige solvencia tecnica con tres proyectos.",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["backend"] == "fake"
    assert "solvencia" in (body["answer"] or "").lower()
    assert body["sources"]


def test_ask_llm_synthesis(monkeypatch):
    import httpx

    from tender_visual_rag import answer as answer_mod
    from tender_visual_rag.config import settings

    monkeypatch.setattr(settings, "openrouter_api_key", "k")

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path.endswith("/chat/completions")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Exige 3 proyectos similares."}}]},
        )

    monkeypatch.setattr(
        answer_mod,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), base_url="https://openrouter.ai/api/v1"),
    )
    body = client.post(
        "/ask",
        json={
            "question": "solvencia",
            "tender_id": "EXP-LLM",
            "document_text": "Se exige solvencia tecnica con tres proyectos similares.",
        },
    ).json()
    assert body["backend"] == "fake+llm"
    assert "3 proyectos" in body["answer"]
