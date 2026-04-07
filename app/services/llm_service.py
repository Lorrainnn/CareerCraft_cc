from __future__ import annotations

import json
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.core.settings import get_settings
from schemas.llm_json import parse_llm_json

T = TypeVar("T", bound=BaseModel)


class LlmService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def chat(self, *, system: str | None = None, user: str, temperature: float = 0.2) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for chat completions")
        body = {
            "model": self.settings.openai_chat_model,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    def chat_json(self, *, system: str | None = None, user: str, model_class: Type[T]) -> T:
        content = self.chat(system=system, user=user)
        return parse_llm_json(content, model_class, max_retries=1)

    def embedding(self, text: str) -> list[float]:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for embeddings")
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self.settings.openai_base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.settings.openai_embedding_model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
        return list(data["data"][0]["embedding"])

    def rerank(self, *, query: str, candidates: list[str], top_n: int) -> list[str]:
        if not candidates:
            return []
        if not self.settings.dashscope_api_key:
            return candidates[:top_n]
        body = {
            "model": self.settings.dashscope_rerank_model,
            "input": {"query": query, "documents": candidates},
            "parameters": {"top_n": top_n, "return_documents": True},
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self.settings.dashscope_base_url.rstrip('/')}/services/rerank/text-rerank/text-rerank",
                headers={
                    "Authorization": f"Bearer {self.settings.dashscope_api_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
        results = data.get("output", {}).get("results", [])
        ranked: list[str] = []
        for item in results:
            document = item.get("document")
            if isinstance(document, dict):
                ranked.append(document.get("text", ""))
            elif isinstance(document, str):
                ranked.append(document)
        return [item for item in ranked if item][:top_n]
