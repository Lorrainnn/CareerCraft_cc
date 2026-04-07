#!/usr/bin/env bash
set -euo pipefail

# Local dev entrypoint
# Example:
#   JWT_SECRET=... REDIS_URL=... QDRANT_HOST=... QDRANT_PORT=... OSS_ENDPOINT=... \
#     OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=... OSS_BUCKET_NAME=... \
#     OPENAI_API_KEY=... DASHSCOPE_API_KEY=... bash run.sh

uvicorn app.main:app --host 0.0.0.0 --port 8000

