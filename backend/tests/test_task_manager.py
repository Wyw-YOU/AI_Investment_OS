import asyncio
import pytest
from app.core.task_manager import TaskManager


@pytest.mark.asyncio
async def test_make_progress_callback():
    tm = TaskManager()
    cb = tm.make_progress_callback("test-task-1")

    await cb("news", "started")
    await cb("news", "completed")

    progress = tm.get_progress("test-task-1")
    assert len(progress) == 2
    assert progress[0]["agent_name"] == "news"
    assert progress[0]["status"] == "started"
    assert progress[1]["status"] == "completed"


@pytest.mark.asyncio
async def test_subscribe_unsubscribe():
    tm = TaskManager()
    queue = tm.subscribe("task-1")
    assert queue is not None

    cb = tm.make_progress_callback("task-1")
    await cb("planner", "started")

    event = await asyncio.wait_for(queue.get(), timeout=1)
    assert event["agent_name"] == "planner"
    assert event["status"] == "started"

    tm.unsubscribe("task-1", queue)


@pytest.mark.asyncio
async def test_concurrent_tasks():
    tm = TaskManager()
    cb1 = tm.make_progress_callback("task-a")
    cb2 = tm.make_progress_callback("task-b")

    await cb1("news", "started")
    await cb2("financial", "started")

    assert len(tm.get_progress("task-a")) == 1
    assert len(tm.get_progress("task-b")) == 1
    assert tm.get_progress("task-a")[0]["agent_name"] == "news"
    assert tm.get_progress("task-b")[0]["agent_name"] == "financial"


@pytest.mark.asyncio
async def test_get_progress_empty():
    tm = TaskManager()
    assert tm.get_progress("nonexistent") == []
