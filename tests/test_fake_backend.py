from tender_visual_rag.backends.fake_backend import FakeBackend

DOCS_A = [
    {"text": "Criterios de adjudicación: precio 40, técnica 60.\nSolvencia técnica exigida."},
    {"text": "Objeto del contrato: plataforma de datos y analítica."},
]
DOCS_B = [{"text": "Obra civil y construcción de edificio."}]


def test_index_counts_pages():
    be = FakeBackend()
    n = be.index("A", DOCS_A)
    assert n == 3  # 2 párrafos del primero + 1 del segundo


def test_query_ranks_relevant_page_first():
    be = FakeBackend()
    be.index("A", DOCS_A)
    hits = be.query("A", "criterios de adjudicación y solvencia", 5)
    assert hits
    assert "doc0/page0" in hits[0].ref  # la página de criterios/solvencia
    assert hits[0].score >= hits[-1].score


def test_query_isolated_by_tender():
    be = FakeBackend()
    be.index("A", DOCS_A)
    be.index("B", DOCS_B)
    hits = be.query("B", "plataforma de datos", 5)
    # 'datos' no está en el expediente B → sin resultados (aislamiento por expediente)
    assert hits == []


def test_query_empty_tender():
    be = FakeBackend()
    assert be.query("missing", "algo", 5) == []
