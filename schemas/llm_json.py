from __future__ import annotations

import json
import re
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


_CODE_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\s*([\s\S]*?)\s*```")


def strip_code_fences(text: str) -> str:
    """
    Remove common markdown code fences around JSON.
    Example:
      ```json { ... } ```
    """
    if not text:
        return text
    # Replace fenced blocks with their content.
    m = _CODE_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def extract_json_candidate(raw: str) -> str:
    """
    Best-effort extraction of the first JSON object/array from model output.
    提示词通常要求模型输出纯 JSON，但这里仍然做一层容错解析。
    """
    if raw is None:
        raise ValueError("LLM output is None")

    text = strip_code_fences(raw)
    start_obj = text.find("{")
    start_arr = text.find("[")

    # Decide which one appears first (if any).
    starts = [(i, "{") for i in [start_obj] if i != -1] + [(i, "[") for i in [start_arr] if i != -1]
    if not starts:
        raise ValueError("No JSON object/array start found in LLM output")

    start, ch = sorted(starts, key=lambda x: x[0])[0]
    end_char = "}" if ch == "{" else "]"
    end = text.rfind(end_char)
    if end == -1 or end < start:
        raise ValueError("No matching JSON end found in LLM output")

    return text[start : end + 1]


def parse_json(raw: str) -> Any:
    candidate = extract_json_candidate(raw)
    return json.loads(candidate)


def parse_llm_json(raw: str, model_class: Type[T], *, max_retries: int = 1) -> T:
    """
    Parse LLM output into a Pydantic model.

    max_retries: only re-attempt extraction/parsing (does not call LLM).
    """
    last_err: Optional[Exception] = None
    for _ in range(max_retries + 1):
        try:
            data = parse_json(raw)
            return model_class.model_validate(data)
        except Exception as e:
            last_err = e

            # Lightweight normalization: if raw is surrounded by quotes, try again.
            if isinstance(raw, str) and raw.strip().startswith('"') and raw.strip().endswith('"'):
                try:
                    unquoted = json.loads(raw)
                    raw = unquoted if isinstance(unquoted, str) else raw
                except Exception:
                    pass

    raise ValueError(f"Failed to parse LLM JSON into {model_class.__name__}: {last_err}")
