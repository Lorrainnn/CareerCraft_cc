import asyncio

import pytest

from app.services.progress_stream import progress_broker


@pytest.mark.asyncio
async def test_progress_broker_emits_progress_and_result():
    stream_id, _ = progress_broker.create()
    await progress_broker.emit(stream_id, "progress", {"message": "working"})
    await progress_broker.emit(stream_id, "result", {"ok": True})
    await progress_broker.close(stream_id)

    messages = []
    async for chunk in progress_broker.iterator(stream_id):
        messages.append(chunk)

    assert any("event: progress" in item for item in messages)
    assert any("event: result" in item for item in messages)
