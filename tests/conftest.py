import pytest

from tender_visual_rag import service
from tender_visual_rag.config import settings


@pytest.fixture(autouse=True)
def fresh_fake_backend(monkeypatch):
    monkeypatch.setattr(settings, "backend", "fake")
    service.reset_backend()
    yield
    service.reset_backend()
