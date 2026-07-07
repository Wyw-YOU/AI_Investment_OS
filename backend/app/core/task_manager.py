"""
任务管理器：管理后台分析任务的生命周期和实时进度推送。

职责：
1. 启动后台 asyncio.Task 执行投资分析
2. 通过 Queue 向 WebSocket 订阅者实时推送 agent 进度事件
3. 定期清理过期任务数据，防止内存泄漏
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        # task_id → 历史事件列表（用于断线重连后回放）
        self._progress: dict[str, list[dict]] = defaultdict(list)
        # task_id → 订阅者队列列表（每个 WebSocket 连接一个队列）
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        # task_id → asyncio.Task（用于跟踪后台任务状态）
        self._tasks: dict[str, asyncio.Task] = {}

    def make_progress_callback(self, task_id: str) -> Callable:
        """创建进度回调函数，注入到 workflow 中，agent 每次状态变化时调用。"""
        async def on_progress(agent_name: str, status: str, detail: dict | None = None):
            event = {
                "agent_name": agent_name,
                "status": status,
                "detail": detail or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._progress[task_id].append(event)
            # 广播给所有订阅此任务的 WebSocket 客户端
            for queue in self._subscribers.get(task_id, []):
                await queue.put(event)
        return on_progress

    def start_background_task(self, task_id: str, coro) -> None:
        """启动后台任务，不阻塞当前请求。完成后自动触发清理。"""
        async_task = asyncio.create_task(coro)
        self._tasks[task_id] = async_task
        async_task.add_done_callback(lambda t: self._cleanup_task(task_id, t))

    def _cleanup_task(self, task_id: str, task: asyncio.Task):
        if task.exception():
            logger.error(f"Background task {task_id} failed: {task.exception()}")
        self._tasks.pop(task_id, None)
        # 向残留的订阅者发送 None 哨兵值，通知它们任务已结束
        for queue in self._subscribers.pop(task_id, []):
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                pass
        self.cleanup_old_tasks()

    def subscribe(self, task_id: str) -> asyncio.Queue:
        """WebSocket 连接时调用，返回一个 Queue 用于接收进度事件。"""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        """WebSocket 断开时调用，移除对应的订阅队列。"""
        subs = self._subscribers.get(task_id, [])
        if queue in subs:
            subs.remove(queue)
        if not subs:
            self._subscribers.pop(task_id, None)

    def get_progress(self, task_id: str) -> list[dict]:
        """获取任务的完整进度历史，用于新连接的 WebSocket 客户端回放。"""
        return list(self._progress.get(task_id, []))

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """清理超过 max_age_seconds 的旧任务数据，由 _cleanup_task 触发。"""
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
