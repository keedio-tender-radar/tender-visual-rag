"""Tests del parser de respuestas de `pixelrag serve` (no requiere modelo)."""

from tender_visual_rag.backends.pixelrag_backend import _parse_hits


def test_parse_results_list_of_lists():
    data = {"results": [[{"page": 3, "score": 0.91, "image": "T1/p3.png"}]]}
    hits = _parse_hits("T1", data)
    assert len(hits) == 1
    assert hits[0].page == 3
    assert hits[0].score == 0.91
    assert hits[0].ref == "T1/p3.png"
    assert hits[0].tender_id == "T1"


def test_parse_hits_alias_and_defaults():
    data = {"hits": [{"doc_id": 2}, {"score": "0.5"}]}
    hits = _parse_hits("T1", data)
    assert hits[0].page == 2
    assert hits[1].score == 0.5


def test_parse_empty():
    assert _parse_hits("T1", {}) == []
