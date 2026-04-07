from schemas.llm_json import parse_llm_json
from schemas.llm_models import CvReview


def test_parse_llm_json_with_code_fence():
    raw = """```json
    {"score": 0.86, "feedback": "结构清晰"}
    ```"""
    result = parse_llm_json(raw, CvReview)
    assert result.score == 0.86
    assert result.feedback == "结构清晰"
