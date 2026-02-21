import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpeechRequest:
    text: str
    agent_id: str
    priority: int = 1
    voice_id: Optional[str] = None
    _counter: int = field(default=0, compare=False, repr=False)


class SpeechQueue:
    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._counter = 0
        self._stop_event = asyncio.Event()
        self.is_interrupted: bool = False

    async def enqueue(self, request: SpeechRequest) -> None:
        self.is_interrupted = False
        self._counter += 1
        request._counter = self._counter
        await self._queue.put((request.priority, self._counter, request))

    async def dequeue(self) -> SpeechRequest:
        _, _, request = await self._queue.get()
        return request

    def qsize(self) -> int:
        return self._queue.qsize()

    def interrupt(self) -> None:
        self.is_interrupted = True
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def stop(self) -> None:
        self._stop_event.set()
