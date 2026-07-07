import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self._progress: dict[str, list[dict]] = defaultdict(list)
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._tasks: dict[str, asyncio.Task] = {}

    def make_progress_callback(self, task_id: str) -> Callable:
        async def on_progress(agent_name: str, status: str, detail: dict | None = None):
            event = {
                "agent_name": agent_name,
                "status": status,
                "detail": detail or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._progress[task_id].append(event)
            for queue in self._subscribers.get(task_id, []):
                await queue.put(event)
        return on_progress

    def start_background_task(self, task_id: str, coro) -> None:
        async_task = asyncio.create_task(coro)
        self._tasks[task_id] = async_task
        async_task.add_done_callback(lambda t: self._cleanup_task(task_id, t))

    def _cleanup_task(self, task_id: str, task: asyncio.Task):
        if task.exception():
            logger.error(f"Background task {task_id} failed: {task.exception()}")
        self._tasks.pop(task_id, None)
        # Close any remaining subscriber queues for this task
        for queue in self._subscribers.pop(task_id, []):
            try:
                queue.put_nowait(None)  # signal subscribers to stop
            except asyncio.QueueFull:
                pass
        self.cleanup_old_tasks()

    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        subs = self._subscribers.get(task_id, [])
        if queue in subs:
            subs.remove(queue)
        if not subs:
            self._subscribers.pop(task_id, None)

    def get_progress(self, task_id: str) -> list[dict]:
        return list(self._progress.get(task_id, []))

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        now = datetime.now(timezone.utc).timestamp()
        to_remove = []
        for task_id, events in self._progress.items():
            if events:
                last_ts = events[-1].get("timestamp", "")
                try:
                    event_time = datetime.fromisoformat(last_ts).timestamp()
                    if now - event_time > max_age_seconds:
                        to_remove.append(task_id)
                except (ValueError, TypeError):
                    pass
        for tid in to_remove:
            self._progress.pop(tid, None)
            self._subscribers.pop(tid, None)


task_manager = TaskManager()
