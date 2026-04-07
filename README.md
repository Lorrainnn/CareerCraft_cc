# CareerCraft — AI-Powered Resume & Interview Platform

> A collaborative learning project focused on production-grade AI engineering — built around a real-world job-seeking use case.

## Overview

CareerCraft is an LLM-powered platform that transforms unstructured resumes into structured, optimizable, and exportable data, then drives job-tailored optimization and mock interviews on top of it.

Core pipeline:
```
Upload → Extract → LLM Parse → Store → RAG Retrieve → Optimize → Export → Interview
```

The project emphasizes engineering depth: async task handling, structured storage, retrieval-augmented generation, streaming feedback, document rendering, and business state management.

---

## Highlights

- **End-to-end resume pipeline** — raw PDF to structured DB, multi-format export, and interview prep in one flow
- **Async parsing architecture** — task table + background worker; returns `taskId` immediately, processes without blocking
- **RAG-based optimization** — HyDE + Embedding + Qdrant + DashScope Rerank for job-tailored resume generation
- **Multi-round scoring loop** — reviewer scores → tailor rewrites, up to 3 iterations, early-exit at `score > 0.8`
- **SSE streaming** — real-time `progress` / `result` events during optimization
- **Multi-format export** — Jinja2 → Markdown → HTML → PDF / DOCX render chain

---

## Architecture

```
app/
├── api/           # HTTP routing
├── services/      # Orchestration (RAG, optimize, interview, render)
├── repositories/  # Data access (cv, resume_task)
├── db/            # SQLAlchemy models & session
└── render/        # Jinja2 templates & export
schemas/           # Pydantic models (CvBO, task/interview responses)
sql/               # MySQL DDL
tests/             # Regression tests
```

**Data model:** Resume is split into a `cv` main table + child tables (`cv_contact`, `cv_education`, `cv_experience`, `cv_project`, `cv_skill`, etc.) for modular edits, RAG reuse, and incremental updates — more maintainable than storing a raw JSON blob.

---

## Key Features

### Async Resume Parsing
Upload returns `taskId` instantly. Background worker handles: file download → PDF text extraction → LLM structured parse (`CvBO`) → MySQL write (main + child tables) → status update. Frontend polls `/task/{taskId}/status`.

### RAG Resume Optimization
1. HyDE generates a hypothetical high-match resume from the JD
2. Embedding → Qdrant search (`minScore=0.7`, `limit × 3` recall)
3. DashScope Rerank (`qwen3-vl-rerank`) narrows to top references
4. Multi-round LLM iteration with per-round feedback + score history

### Mock Interview (Lightweight Agent Orchestration)
- `start` — loads resume + JD, generates interview plan and first question
- `continue` — reflects on answer → decides: follow-up / next question / next stage / end
- `status / finish` — returns progress and final evaluation

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | FastAPI, SQLAlchemy, PyMySQL, Redis |
| AI / Retrieval | OpenAI-compatible Chat & Embedding, DashScope Rerank, HyDE |
| Document | pypdf, Jinja2, CommonMark, WeasyPrint, LibreOffice |
| Storage | MySQL, Qdrant, Redis, local OSS fallback |

---

## API Endpoints

```
POST  /api/v1/resumes/upload
GET   /api/v1/resumes/task/{taskId}/status
POST  /api/v1/resumes/optimize
GET   /api/v1/resumes/optimize/stream
POST  /api/v1/resumes/generateOptimizedFile
POST  /api/v1/resumes/{resume_id}/embedding
POST  /api/v1/interviews/sessions
POST  /api/v1/interviews/sessions/{id}/continue
GET   /api/v1/interviews/sessions/{id}/status
POST  /api/v1/interviews/sessions/{id}/finish
```

---

## Quick Start

```bash
# Start infrastructure
docker compose up -d mysql redis qdrant

# Init database
mysql -u root -p < sql/cv.sql

# Install & run
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Required env vars:**
`DATABASE_URL` · `JWT_SECRET` · `OPENAI_API_KEY` · `OPENAI_BASE_URL` · `OPENAI_CHAT_MODEL` · `OPENAI_EMBEDDING_MODEL` · `DASHSCOPE_API_KEY` · `DASHSCOPE_RERANK_MODEL` · `QDRANT_HOST/PORT/COLLECTION_NAME` · `REDIS_URL` · `OSS_BUCKET_NAME`

> Local fallback: files stored under `.oss/<bucket>/<key>` for offline development.

---

## Tests

```bash
pytest
```

| File | Coverage |
|---|---|
| `test_llm_json.py` | LLM JSON cleaning & structured parse |
| `test_rag_service.py` | RAG retrieval parameter validation |
| `test_resume_task_repository.py` | Task state transitions & `resume_id` backfill |
| `test_resume_sse.py` | SSE `progress` and `result` event delivery |

---
