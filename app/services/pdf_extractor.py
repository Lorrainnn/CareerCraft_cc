from __future__ import annotations

from io import BytesIO
from typing import Callable


class PdfExtractor:
    def __init__(self) -> None:
        self._extractors: list[tuple[str, Callable[[bytes], str]]] = [
            ("pypdf", self._extract_pypdf),
            ("pdfminer", self._extract_pdfminer),
        ]

    def extract_text(self, content: bytes) -> str:
        candidates: list[tuple[int, str]] = []
        for _, extractor in self._extractors:
            try:
                text = extractor(content)
            except Exception:
                continue
            if text.strip():
                score = self._score(text)
                candidates.append((score, text))
        if not candidates:
            raise RuntimeError("No PDF extractor available. Install pypdf or pdfminer.six.")
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _score(self, text: str) -> int:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return len(lines) * 5 + min(len(text), 5000)

    def _extract_pypdf(self, content: bytes) -> str:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        chunks: list[str] = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)

    def _extract_pdfminer(self, content: bytes) -> str:
        from pdfminer.high_level import extract_text

        return extract_text(BytesIO(content))
