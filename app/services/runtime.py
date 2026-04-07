from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor


resume_worker_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="resume-worker")
optimize_worker_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="optimize-worker")
