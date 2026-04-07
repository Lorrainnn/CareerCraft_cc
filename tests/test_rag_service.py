from app.services.rag_service import ResumeRagService


class FakeLlmService:
    def __init__(self):
        self.rerank_args = None

    def chat(self, **kwargs):
        return "fake hypothetical resume"

    def embedding(self, text: str):
        return [0.1, 0.2, 0.3]

    def rerank(self, *, query: str, candidates: list[str], top_n: int):
        self.rerank_args = {"query": query, "candidates": candidates, "top_n": top_n}
        return candidates[:top_n]


class FakeResult:
    def __init__(self, text: str):
        self.payload = {"content": text}


class FakeQdrantClient:
    def __init__(self, *args, **kwargs):
        self.search_args = None

    def get_collection(self, *args, **kwargs):
        raise RuntimeError("missing")

    def recreate_collection(self, *args, **kwargs):
        return None

    def search(self, **kwargs):
        self.search_args = kwargs
        return [FakeResult("candidate-1"), FakeResult("candidate-2"), FakeResult("candidate-3")]


def test_retrieve_templates_uses_expected_parameters(monkeypatch):
    fake_llm = FakeLlmService()
    fake_client = FakeQdrantClient()

    service = ResumeRagService(fake_llm)
    monkeypatch.setattr(service, "_client", lambda: fake_client)
    result = service.retrieve_templates("python backend jd", 2)

    assert fake_client.search_args["score_threshold"] == 0.7
    assert fake_client.search_args["limit"] == 6
    assert fake_llm.rerank_args["top_n"] == 2
    assert result == ["candidate-1", "candidate-2"]
