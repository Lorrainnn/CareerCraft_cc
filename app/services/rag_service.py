from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.settings import get_settings
from app.services.llm_service import LlmService
from schemas.cv_models import CvBO


class ResumeRagService:
    def __init__(self, llm_service: LlmService) -> None:
        self.llm_service = llm_service
        self.settings = get_settings()

    def store_cv(self, cv: CvBO, *, payload: dict[str, Any] | None = None) -> None:
        from qdrant_client.http import models

        content = self._cv_to_text(cv)
        if not content.strip():
            return
        vector = self.llm_service.embedding(content)
        client = self._client()
        self.ensure_collection(client, len(vector))
        client.upsert(
            collection_name=self.settings.qdrant_collection_name,
            points=[
                models.PointStruct(
                    id=(payload or {}).get("resume_id") or uuid4().hex,
                    vector=vector,
                    payload={"content": content, **(payload or {})},
                )
            ],
        )

    def retrieve_templates(self, query: str, limit: int) -> list[str]:
        if not query.strip():
            return []
        hyde_prompt = (
            "请根据以下职位描述，生成一份高度匹配的候选人简历摘要和核心技能列表。"
            "主要包含Summary和Skills部分即可，不要包含虚构的联系方式。\n\n职位描述：\n"
            + query
        )
        hypothetical_resume = self.llm_service.chat(user=hyde_prompt)
        embedding = self.llm_service.embedding(hypothetical_resume or query)
        client = self._client()
        self.ensure_collection(client, len(embedding))
        recall_limit = max(limit * 3, limit)
        results = client.search(
            collection_name=self.settings.qdrant_collection_name,
            query_vector=embedding,
            limit=recall_limit,
            score_threshold=0.7,
            with_payload=True,
        )
        candidates = [
            (item.payload or {}).get("content", "")
            for item in results
            if ((item.payload or {}).get("content", ""))
        ]
        return self.llm_service.rerank(query=query, candidates=candidates, top_n=limit)

    def ensure_collection(self, client: Any, vector_size: int) -> None:
        from qdrant_client.http import models

        recreate = False
        try:
            info = client.get_collection(self.settings.qdrant_collection_name)
            config = getattr(info, "config", None)
            params = getattr(config, "params", None)
            vectors = getattr(params, "vectors", None)
            existing_size = None
            if hasattr(vectors, "size"):
                existing_size = vectors.size
            elif isinstance(vectors, dict):
                first = next(iter(vectors.values()))
                existing_size = getattr(first, "size", None)
            if existing_size and int(existing_size) != int(vector_size):
                recreate = True
        except Exception:
            recreate = True

        if recreate:
            try:
                client.delete_collection(self.settings.qdrant_collection_name)
            except Exception:
                pass
            client.recreate_collection(
                collection_name=self.settings.qdrant_collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    def _client(self):
        from qdrant_client import QdrantClient

        return QdrantClient(host=self.settings.qdrant_host, port=self.settings.qdrant_port)

    def _cv_to_text(self, cv: CvBO) -> str:
        parts: list[str] = []
        if cv.summary:
            parts.append(f"Summary:\n{cv.summary}")
        if cv.skills:
            skills = []
            for skill in cv.skills:
                if not skill.name:
                    continue
                desc = skill.name
                if skill.highlights:
                    highlights = "; ".join(hl.highlight or "" for hl in skill.highlights if hl.highlight)
                    if highlights:
                        desc += f" ({highlights})"
                skills.append(desc)
            if skills:
                parts.append("Skills:\n" + ", ".join(skills))
        if cv.experiences:
            lines = []
            for exp in cv.experiences:
                lines.append(f"- {exp.industry or ''} at {exp.company or ''}")
                if exp.description:
                    lines.append(f"  Description: {exp.description}")
                for hl in exp.highlights:
                    if hl.highlight:
                        lines.append(f"  Highlight: {hl.highlight}")
            parts.append("Work Experience:\n" + "\n".join(lines))
        if cv.projects:
            lines = []
            for proj in cv.projects:
                lines.append(f"- {proj.name or ''}")
                if proj.description:
                    lines.append(f"  Description: {proj.description}")
                for hl in proj.highlights:
                    if hl.highlight:
                        lines.append(f"  Highlight: {hl.highlight}")
            parts.append("Projects:\n" + "\n".join(lines))
        if cv.educations:
            lines = [f"- {edu.school or ''}, {edu.major or ''}, {edu.degree or ''}" for edu in cv.educations]
            parts.append("Education:\n" + "\n".join(lines))
        return "\n\n".join(part for part in parts if part)
