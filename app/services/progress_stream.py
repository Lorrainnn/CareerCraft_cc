from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator


class ProgressBroker:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[str | None]] = {}

    def create(self) -> tuple[str, asyncio.Queue[str | None]]:
        stream_id = uuid.uuid4().hex
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._queues[stream_id] = queue
        return stream_id, queue

    async def emit(self, stream_id: str, event: str, data: object) -> None:
        queue = self._queues.get(stream_id)
        if queue is None:
            return
        payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        await queue.put(payload)

    async def close(self, stream_id: str) -> None:
        queue = self._queues.get(stream_id)
        if queue is not None:
            await queue.put(None)

    async def iterator(self, stream_id: str) -> AsyncIterator[str]:
        queue = self._queues[stream_id]
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item
        self._queues.pop(stream_id, None)


progress_broker = ProgressBroker()
