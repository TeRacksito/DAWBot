import heapq
import threading
from typing import Union
from typing import Optional
import asyncio
from asyncio import Lock

class PriorityQueue:
    def __init__(self, queue: Optional[list[tuple[int, list[str]]]] = None):
        if queue is None:
            queue = list()
        self._queue = queue
        self.lock = Lock()

    def addJob(self, job: list[str], priority: int) -> None:
        with self.lock:
            heapq.heappush(self._queue, (priority, job))

    def clear(self):
        with self.lock:
            queue = self._queue.copy()
            self._queue.clear()
            return queue

    def getLength(self):
        with self.lock:
            return len(self._queue)
