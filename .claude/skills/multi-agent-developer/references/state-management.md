# State Management Reference

Comprehensive guide to designing and implementing state management in multi-agent systems.

---

## Table of Contents

1. [State Design Principles](#1-state-design-principles)
2. [State Schema Patterns](#2-state-schema-patterns)
3. [State Transitions](#3-state-transitions)
4. [Memory Systems](#4-memory-systems)
5. [Persistence Strategies](#5-persistence-strategies)
6. [State Synchronization](#6-state-synchronization)
7. [Common Patterns and Anti-Patterns](#7-common-patterns-and-anti-patterns)
8. [Implementation Examples](#8-implementation-examples)

---

## 1. State Design Principles

### Principle 1: Immutability

State should be immutable between workflow nodes. Each node receives state and returns a new state, never modifying the input.

```python
# CORRECT: Return new state
def agent_node(state: dict) -> dict:
    result = analyze(state)
    return {**state, "analysis": result}  # New dict with merged data

# WRONG: Mutate existing state
def agent_node(state: dict) -> dict:
    state["analysis"] = analyze(state)  # Mutation!
    return state
```

**Why immutability matters:**
- Enables safe parallel execution
- Prevents race conditions
- Makes state changes explicit and traceable
- Simplifies debugging and replay

### Principle 2: Minimal State

Only include data that's actually needed. Avoid storing everything "just in case."

```python
# GOOD: Minimal state
class AgentState(TypedDict):
    stock_code: str
    market_data: dict
    agent_results: dict
    final_report: Optional[dict]

# BAD: Bloated state
class AgentState(TypedDict):
    stock_code: str
    market_data: dict
    historical_data: list  # Not needed in most nodes
    raw_api_responses: dict  # Implementation detail
    debug_logs: list  # Should be in logging system
    temp_calculations: dict  # Intermediate, not state
```

**Benefits of minimal state:**
- Reduced memory usage
- Faster serialization/deserialization
- Clearer data flow
- Easier to debug

### Principle 3: Well-Typed State

Use type hints and validation to catch errors early:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentOutput(BaseModel):
    agent_name: str
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentState(BaseModel):
    """Well-typed state with validation."""

    # Core identifiers
    task_id: str
    stock_code: str = Field(pattern=r'^[A-Z]{1,5}$')

    # Input data
    query: str
    market_data: Dict[str, Any] = {}

    # Agent outputs
    agent_outputs: Dict[str, AgentOutput] = {}

    # Final results
    final_report: Optional[Dict[str, Any]] = None

    # Workflow metadata
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = []

    class Config:
        # Allow arbitrary types for complex data
        arbitrary_types_allowed = True
```

### Principle 4: Explicit Data Flow

Make data dependencies explicit in the state structure:

```python
# GOOD: Clear data flow
class InvestmentState(TypedDict):
    # Input
    stock_code: str
    user_query: str

    # Collected data (from data agents)
    market_data: dict
    news_data: list
    financial_data: dict

    # Analysis results (from analysis agents)
    news_analysis: Optional[dict]
    financial_analysis: Optional[dict]
    technical_analysis: Optional[dict]

    # Synthesis (from synthesis agents)
    risk_assessment: Optional[dict]
    final_report: Optional[dict]

# This makes it clear:
# - market_data, news_data, financial_data are inputs
# - *_analysis are intermediate results
# - final_report is the output
```

---

## 2. State Schema Patterns

### Pattern A: TypedDict (LangGraph Standard)

```python
from typing import TypedDict, Annotated, Optional, List, Dict, Any
import operator

class WorkflowState(TypedDict):
    # Required fields
    task_id: str
    stock_code: str

    # Optional fields with defaults
    market_data: Dict[str, Any]
    news_data: List[Dict[str, Any]]

    # Parallel results (collected via operator.add)
    agent_results: Annotated[List[Dict], operator.add]

    # Final output
    final_report: Optional[Dict[str, Any]]

    # Metadata
    errors: Annotated[List[str], operator.add]
```

**Use case:** LangGraph workflows with parallel execution.

### Pattern B: Pydantic BaseModel

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentState(BaseModel):
    """State with validation and serialization."""

    task_id: str
    stock_code: str

    market_data: Dict[str, Any] = {}
    agent_outputs: Dict[str, Dict[str, Any]] = {}

    final_report: Optional[Dict[str, Any]] = None

    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('stock_code')
    def validate_stock_code(cls, v):
        if not v.isalpha() or len(v) > 5:
            raise ValueError('Invalid stock code')
        return v.upper()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Use case:** When you need validation, serialization, or complex state logic.

### Pattern C: Dataclass (Simple Cases)

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class SimpleState:
    """Lightweight state for simple workflows."""

    task_id: str
    stock_code: str

    market_data: Dict[str, Any] = field(default_factory=dict)
    analysis_result: Optional[Dict[str, Any]] = None

    def update(self, **kwargs) -> 'SimpleState':
        """Create new state with updates."""
        from dataclasses import replace
        return replace(self, **kwargs)
```

**Use case:** Simple workflows without complex validation needs.

### Pattern D: State with History

```python
from typing import TypedDict, List, Dict, Any
from datetime import datetime

class StateSnapshot(TypedDict):
    timestamp: datetime
    state: Dict[str, Any]
    trigger: str  # Which node created this snapshot

class StateWithHistory(TypedDict):
    """State that tracks its own evolution."""

    # Current state
    current: Dict[str, Any]

    # History of state changes
    history: List[StateSnapshot]

    # Version tracking
    version: int
    created_at: datetime

def add_snapshot(state: StateWithHistory, trigger: str) -> StateWithHistory:
    """Add current state to history."""
    snapshot = {
        "timestamp": datetime.now(),
        "state": state["current"].copy(),
        "trigger": trigger
    }

    return {
        **state,
        "history": state["history"] + [snapshot],
        "version": state["version"] + 1
    }
```

**Use case:** When you need audit trails or undo capabilities.

---

## 3. State Transitions

### Transition Functions

Define explicit transition functions for clarity:

```python
def transition_to_analysis(state: AgentState) -> AgentState:
    """Transition from data collection to analysis phase."""
    return {
        **state,
        "status": "analyzing",
        "phase": "analysis",
        "started_analysis_at": datetime.now()
    }

def add_agent_result(
    state: AgentState,
    agent_name: str,
    result: dict
) -> AgentState:
    """Add an agent's result to state."""
    return {
        **state,
        "agent_outputs": {
            **state["agent_outputs"],
            agent_name: result
        }
    }

def transition_to_completed(
    state: AgentState,
    final_report: dict
) -> AgentState:
    """Transition to completed state."""
    return {
        **state,
        "status": "completed",
        "final_report": final_report,
        "completed_at": datetime.now()
    }
```

### State Machine Pattern

```python
from enum import Enum
from typing import Callable, Dict

class WorkflowPhase(str, Enum):
    INITIALIZATION = "initialization"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    COMPLETED = "completed"
    FAILED = "failed"

# Valid transitions
TRANSITIONS: Dict[WorkflowPhase, List[WorkflowPhase]] = {
    WorkflowPhase.INITIALIZATION: [WorkflowPhase.DATA_COLLECTION, WorkflowPhase.FAILED],
    WorkflowPhase.DATA_COLLECTION: [WorkflowPhase.ANALYSIS, WorkflowPhase.FAILED],
    WorkflowPhase.ANALYSIS: [WorkflowPhase.SYNTHESIS, WorkflowPhase.FAILED],
    WorkflowPhase.SYNTHESIS: [WorkflowPhase.COMPLETED, WorkflowPhase.FAILED],
    WorkflowPhase.COMPLETED: [],
    WorkflowPhase.FAILED: []
}

def can_transition(current: WorkflowPhase, target: WorkflowPhase) -> bool:
    """Check if transition is valid."""
    return target in TRANSITIONS.get(current, [])

def transition(
    state: AgentState,
    target_phase: WorkflowPhase
) -> AgentState:
    """Perform validated state transition."""
    current_phase = WorkflowPhase(state["phase"])

    if not can_transition(current_phase, target_phase):
        raise ValueError(
            f"Invalid transition: {current_phase} -> {target_phase}"
        )

    return {
        **state,
        "phase": target_phase.value,
        "previous_phase": current_phase.value,
        "transitioned_at": datetime.now()
    }
```

---

## 4. Memory Systems

### Short-Term Memory (Workflow State)

In-memory state that exists only during workflow execution:

```python
class ShortTermMemory:
    """Memory that persists within a single workflow execution."""

    def __init__(self):
        self._memory: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> None:
        """Store a value."""
        self._memory[key] = value

    def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve a value."""
        return self._memory.get(key, default)

    def get_context(self, keys: List[str] = None) -> Dict[str, Any]:
        """Get memory context for prompt injection."""
        if keys:
            return {k: self._memory[k] for k in keys if k in self._memory}
        return self._memory.copy()

    def clear(self) -> None:
        """Clear all memory."""
        self._memory.clear()

# Usage in workflow
class WorkflowWithMemory:
    def __init__(self):
        self.memory = ShortTermMemory()

    def data_collection_node(self, state: dict) -> dict:
        # Store intermediate results in memory
        self.memory.store("raw_data", state["market_data"])
        self.memory.store("collection_timestamp", datetime.now())

        return state

    def analysis_node(self, state: dict) -> dict:
        # Retrieve from memory
        raw_data = self.memory.retrieve("raw_data")
        collection_time = self.memory.retrieve("collection_timestamp")

        # Use in analysis
        result = analyze(raw_data, collection_time)

        return {**state, "analysis": result}
```

### Long-Term Memory (Persistent)

Memory that persists across workflow executions:

```python
import json
from pathlib import Path
from datetime import datetime

class LongTermMemory:
    """Persistent memory stored on disk or database."""

    def __init__(self, storage_path: str = "./memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def store(self, namespace: str, key: str, value: Any) -> None:
        """Store a value persistently."""
        file_path = self.storage_path / namespace / f"{key}.json"
        file_path.parent.mkdir(exist_ok=True)

        data = {
            "value": value,
            "stored_at": datetime.now().isoformat(),
            "namespace": namespace,
            "key": key
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def retrieve(self, namespace: str, key: str) -> Optional[Any]:
        """Retrieve a value."""
        file_path = self.storage_path / namespace / f"{key}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get("value")

    def search(self, namespace: str, query: str = None) -> List[Dict]:
        """Search memory by namespace and optional query."""
        results = []
        namespace_path = self.storage_path / namespace

        if not namespace_path.exists():
            return results

        for file_path in namespace_path.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)

                if query is None or query in str(data["value"]):
                    results.append(data)

        return results

# Usage
memory = LongTermMemory()

# Store analysis results
memory.store(
    namespace="stock_analysis",
    key="AAPL_2024-01-15",
    value={
        "recommendation": "BUY",
        "confidence": 0.85,
        "price_target": 185
    }
)

# Retrieve previous analysis
previous = memory.retrieve("stock_analysis", "AAPL_2024-01-15")
```

### Episodic Memory (Recent Context)

Memory that maintains recent interaction context:

```python
from collections import deque
from typing import Deque

class EpisodicMemory:
    """Memory that maintains recent context within a session."""

    def __init__(self, max_episodes: int = 10):
        self.episodes: Deque[Dict] = deque(maxlen=max_episodes)

    def add_episode(self, episode: Dict) -> None:
        """Add a new episode."""
        episode["timestamp"] = datetime.now()
        self.episodes.append(episode)

    def get_recent(self, n: int = 5) -> List[Dict]:
        """Get N most recent episodes."""
        return list(self.episodes)[-n:]

    def get_context(self, include_timestamps: bool = False) -> str:
        """Format recent episodes for prompt injection."""
        context_parts = []

        for i, episode in enumerate(self.get_recent()):
            if include_timestamps:
                ts = episode.get("timestamp", "unknown")
                context_parts.append(f"[{ts}] Episode {i+1}:")
            else:
                context_parts.append(f"Episode {i+1}:")

            for key, value in episode.items():
                if key != "timestamp":
                    context_parts.append(f"  {key}: {value}")

            context_parts.append("")

        return "\n".join(context_parts)

# Usage in agent
class ContextAwareAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.episodic_memory = EpisodicMemory()

    def run(self, state: dict) -> dict:
        # Get recent context
        recent_context = self.episodic_memory.get_context()

        # Add to state for prompt
        enhanced_state = {
            **state,
            "recent_interactions": recent_context
        }

        # Execute analysis
        result = super().run(enhanced_state)

        # Store this interaction
        self.episodic_memory.add_episode({
            "stock": state.get("stock_code"),
            "query": state.get("query"),
            "result_summary": result.get("summary", "")
        })

        return result
```

### Vector Memory (Semantic Search)

Memory with semantic search capabilities:

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple

class VectorMemory:
    """Memory with semantic search using embeddings."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.memories: List[Dict] = []
        self.embeddings: List[np.ndarray] = []

    def store(self, content: str, metadata: Dict = None) -> None:
        """Store a memory with its embedding."""
        embedding = self.model.encode(content)

        self.memories.append({
            "content": content,
            "metadata": metadata or {},
            "stored_at": datetime.now()
        })
        self.embeddings.append(embedding)

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[Dict, float]]:
        """Search memories by semantic similarity."""
        if not self.embeddings:
            return []

        query_embedding = self.model.encode(query)

        # Calculate similarities
        similarities = [
            np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            for emb in self.embeddings
        ]

        # Get top-k results above threshold
        results = []
        for idx in np.argsort(similarities)[::-1][:top_k]:
            if similarities[idx] >= threshold:
                results.append((self.memories[idx], similarities[idx]))

        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        """Get relevant memories for prompt injection."""
        results = self.search(query, top_k=top_k)

        if not results:
            return "No relevant memories found."

        context_parts = []
        for memory, score in results:
            context_parts.append(
                f"[Relevance: {score:.2f}] {memory['content']}"
            )

        return "\n---\n".join(context_parts)

# Usage
vector_memory = VectorMemory()

# Store past analyses
vector_memory.store(
    "AAPL shows strong uptrend with price above 50-day and 200-day moving averages. BUY with 85% confidence.",
    metadata={"stock": "AAPL", "date": "2024-01-10"}
)

# Search for relevant context
context = vector_memory.get_context("What's the technical outlook for Apple?")
```

---

## 5. Persistence Strategies

### Strategy A: File-Based Persistence

```python
import json
import pickle
from pathlib import Path
from datetime import datetime

class FileStatePersistence:
    """Persist state to files."""

    def __init__(self, base_path: str = "./state"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def save_state(
        self,
        state_id: str,
        state: dict,
        format: str = "json"
    ) -> Path:
        """Save state to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{state_id}_{timestamp}.{format}"
        file_path = self.base_path / filename

        if format == "json":
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        elif format == "pickle":
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)

        return file_path

    def load_state(self, file_path: Path) -> dict:
        """Load state from file."""
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                return json.load(f)
        elif file_path.suffix == '.pkl':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")

    def list_states(self, state_id: str = None) -> List[Path]:
        """List saved states."""
        if state_id:
            return list(self.base_path.glob(f"{state_id}_*"))
        return list(self.base_path.glob("*"))

    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """Remove states older than max_age_days."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0

        for file_path in self.base_path.glob("*"):
            if file_path.stat().st_mtime < cutoff.timestamp():
                file_path.unlink()
                removed += 1

        return removed
```

### Strategy B: Database Persistence

```python
import sqlite3
import json
from datetime import datetime

class SQLiteStatePersistence:
    """Persist state to SQLite database."""

    def __init__(self, db_path: str = "./state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_states (
                    state_id TEXT PRIMARY KEY,
                    workflow_type TEXT,
                    state_data TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_id TEXT,
                    version INTEGER,
                    state_data TEXT,
                    trigger_node TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (state_id) REFERENCES workflow_states(state_id)
                )
            """)

    def save_state(
        self,
        state_id: str,
        state: dict,
        workflow_type: str = None
    ) -> None:
        """Save or update state."""
        now = datetime.now()
        state_json = json.dumps(state, default=str)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_states
                (state_id, workflow_type, state_data, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                state_id,
                workflow_type,
                state_json,
                state.get("status", "unknown"),
                now,
                now
            ))

    def load_state(self, state_id: str) -> Optional[dict]:
        """Load state by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state_data FROM workflow_states WHERE state_id = ?",
                (state_id,)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row[0])
            return None

    def add_history(
        self,
        state_id: str,
        state: dict,
        trigger_node: str
    ) -> None:
        """Add state to history."""
        now = datetime.now()
        state_json = json.dumps(state, default=str)

        with sqlite3.connect(self.db_path) as conn:
            # Get current version
            cursor = conn.execute(
                "SELECT MAX(version) FROM state_history WHERE state_id = ?",
                (state_id,)
            )
            max_version = cursor.fetchone()[0] or 0

            conn.execute("""
                INSERT INTO state_history
                (state_id, version, state_data, trigger_node, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (state_id, max_version + 1, state_json, trigger_node, now))

    def get_history(self, state_id: str) -> List[dict]:
        """Get state history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT version, state_data, trigger_node, created_at
                FROM state_history
                WHERE state_id = ?
                ORDER BY version
            """, (state_id,))

            return [
                {
                    "version": row[0],
                    "state": json.loads(row[1]),
                    "trigger": row[2],
                    "timestamp": row[3]
                }
                for row in cursor.fetchall()
            ]
```

### Strategy C: Redis Persistence (for Distributed Systems)

```python
import redis
import json
from typing import Optional

class RedisStatePersistence:
    """Persist state to Redis for distributed systems."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "workflow:"
    ):
        self.redis = redis.from_url(redis_url)
        self.prefix = prefix

    def _key(self, state_id: str) -> str:
        """Generate Redis key."""
        return f"{self.prefix}{state_id}"

    def save_state(
        self,
        state_id: str,
        state: dict,
        ttl: int = 86400  # 24 hours default
    ) -> None:
        """Save state with optional TTL."""
        key = self._key(state_id)
        state_json = json.dumps(state, default=str)

        self.redis.setex(key, ttl, state_json)

    def load_state(self, state_id: str) -> Optional[dict]:
        """Load state."""
        key = self._key(state_id)
        state_json = self.redis.get(key)

        if state_json:
            return json.loads(state_json)
        return None

    def delete_state(self, state_id: str) -> bool:
        """Delete state."""
        key = self._key(state_id)
        return self.redis.delete(key) > 0

    def update_state(
        self,
        state_id: str,
        updates: dict
    ) -> Optional[dict]:
        """Atomically update state fields."""
        key = self._key(state_id)

        # Use pipeline for atomic operation
        with self.redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)
                    state_json = pipe.get(key)

                    if not state_json:
                        return None

                    state = json.loads(state_json)
                    state.update(updates)

                    pipe.multi()
                    pipe.set(key, json.dumps(state, default=str))
                    pipe.execute()

                    return state

                except redis.WatchError:
                    continue

    def list_states(self, pattern: str = "*") -> list:
        """List all states matching pattern."""
        keys = self.redis.keys(f"{self.prefix}{pattern}")
        return [key.decode().replace(self.prefix, '') for key in keys]
```

---

## 6. State Synchronization

### Parallel Execution Synchronization

When multiple agents run in parallel, their state updates need careful handling:

```python
from typing import TypedDict, Annotated
import operator

class ParallelState(TypedDict):
    # Shared state
    stock_code: str
    market_data: dict

    # Parallel results collected safely
    agent_results: Annotated[list, operator.add]

    # Synchronization flag
    all_agents_complete: bool

# LangGraph handles this automatically with Annotated[list, operator.add]
# Each parallel agent appends to the list, and LangGraph merges them
```

### Manual Synchronization (if needed)

```python
import asyncio
from typing import Dict, Any

class StateSynchronizer:
    """Synchronize state updates from parallel agents."""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.pending_updates: Dict[str, Any] = {}

    async def submit_update(
        self,
        agent_id: str,
        update: Dict[str, Any]
    ) -> None:
        """Submit an update from an agent."""
        async with self.lock:
            self.pending_updates[agent_id] = update

    async def apply_updates(self, state: dict) -> dict:
        """Apply all pending updates to state."""
        async with self.lock:
            new_state = state.copy()

            for agent_id, update in self.pending_updates.items():
                # Merge update into state
                new_state[f"{agent_id}_result"] = update

            # Clear pending updates
            self.pending_updates.clear()

            return new_state

    def get_pending_count(self) -> int:
        """Get number of pending updates."""
        return len(self.pending_updates)
```

### Event-Based Synchronization

```python
import asyncio
from typing import Callable, Dict, List

class EventEmitter:
    """Event-based state synchronization."""

    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Register event listener."""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)

    async def emit(self, event: str, data: Any) -> None:
        """Emit event to all listeners."""
        if event in self.listeners:
            tasks = [
                asyncio.create_task(callback(data))
                for callback in self.listeners[event]
            ]
            await asyncio.gather(*tasks)

# Usage
emitter = EventEmitter()

# Agent 1 emits when complete
async def news_agent(state, emitter):
    result = await analyze_news(state)
    await emitter.emit("news_complete", result)
    return result

# Agent 2 listens and updates state
async def on_news_complete(result, state):
    state["news_analysis"] = result
    return state

emitter.on("news_complete", lambda r: on_news_complete(r, state))
```

---

## 7. Common Patterns and Anti-Patterns

### Anti-Pattern 1: Mutable Shared State

```python
# WRONG: Agents share and mutate same state
class BadAgent:
    def run(self, state):
        state["result"] = self.analyze(state)  # Mutation!
        return state

# CORRECT: Return new state
class GoodAgent:
    def run(self, state):
        result = self.analyze(state)
        return {**state, "result": result}  # New state
```

### Anti-Pattern 2: God State

```python
# WRONG: Everything in one massive state
class GodState(TypedDict):
    user_data: dict
    market_data: dict
    news_data: list
    financial_data: dict
    technical_data: dict
    analysis_results: dict
    reports: list
    chat_history: list
    user_preferences: dict
    system_config: dict
    debug_info: dict
    # ... 50 more fields

# CORRECT: Focused state per workflow
class AnalysisState(TypedDict):
    stock_code: str
    market_data: dict
    analysis_results: dict
```

### Anti-Pattern 3: State as Global Variable

```python
# WRONG: Global mutable state
GLOBAL_STATE = {}

class BadAgent:
    def run(self, state):
        GLOBAL_STATE["result"] = self.analyze()  # Global mutation!
        return GLOBAL_STATE

# CORRECT: Pass state explicitly
class GoodAgent:
    def run(self, state):
        result = self.analyze(state)
        return {**state, "result": result}
```

### Pattern 1: State Versioning

```python
def versioned_state_update(state: dict, updates: dict) -> dict:
    """Update state with version tracking."""
    return {
        **state,
        **updates,
        "version": state.get("version", 0) + 1,
        "updated_at": datetime.now()
    }
```

### Pattern 2: State Validation

```python
def validate_state_transition(
    old_state: dict,
    new_state: dict,
    allowed_changes: list
) -> bool:
    """Validate that only allowed fields changed."""
    for key in new_state:
        if key not in old_state and key not in allowed_changes:
            raise ValueError(f"Unexpected new field: {key}")
        if key in old_state and old_state[key] != new_state[key]:
            if key not in allowed_changes:
                raise ValueError(f"Unexpected change to: {key}")
    return True
```

### Pattern 3: State Compression

```python
def compress_state(state: dict) -> dict:
    """Compress state by removing unnecessary data."""
    compressed = state.copy()

    # Remove large fields not needed downstream
    if "raw_data" in compressed:
        del compressed["raw_data"]
    if "debug_logs" in compressed:
        del compressed["debug_logs"]

    # Summarize large collections
    if "all_news" in compressed and len(compressed["all_news"]) > 10:
        compressed["news_summary"] = summarize_news(compressed["all_news"])
        del compressed["all_news"]

    return compressed
```

---

## 8. Implementation Examples

### Complete State Management System

```python
from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json

class WorkflowPhase(str, Enum):
    INIT = "init"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"

class InvestmentState(TypedDict):
    # Identifiers
    task_id: str
    stock_code: str
    user_id: str

    # Workflow tracking
    phase: str
    version: int

    # Input data
    query: str
    market_data: Dict[str, Any]

    # Agent outputs
    news_analysis: Optional[Dict[str, Any]]
    financial_analysis: Optional[Dict[str, Any]]
    technical_analysis: Optional[Dict[str, Any]]

    # Synthesis
    risk_assessment: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # Metadata
    created_at: str
    updated_at: str
    errors: List[str]

class StateManager:
    """Complete state management system."""

    def __init__(self, persistence=None, memory=None):
        self.persistence = persistence
        self.memory = memory

    def create_initial_state(
        self,
        task_id: str,
        stock_code: str,
        user_id: str,
        query: str
    ) -> InvestmentState:
        """Create initial workflow state."""
        now = datetime.now().isoformat()

        return {
            "task_id": task_id,
            "stock_code": stock_code,
            "user_id": user_id,
            "phase": WorkflowPhase.INIT.value,
            "version": 1,
            "query": query,
            "market_data": {},
            "news_analysis": None,
            "financial_analysis": None,
            "technical_analysis": None,
            "risk_assessment": None,
            "final_report": None,
            "created_at": now,
            "updated_at": now,
            "errors": []
        }

    def transition_phase(
        self,
        state: InvestmentState,
        target_phase: WorkflowPhase
    ) -> InvestmentState:
        """Transition to new phase with validation."""
        current = WorkflowPhase(state["phase"])

        # Validate transition
        valid_transitions = {
            WorkflowPhase.INIT: [WorkflowPhase.COLLECTING, WorkflowPhase.FAILED],
            WorkflowPhase.COLLECTING: [WorkflowPhase.ANALYZING, WorkflowPhase.FAILED],
            WorkflowPhase.ANALYZING: [WorkflowPhase.SYNTHESIZING, WorkflowPhase.FAILED],
            WorkflowPhase.SYNTHESIZING: [WorkflowPhase.COMPLETE, WorkflowPhase.FAILED],
            WorkflowPhase.COMPLETE: [],
            WorkflowPhase.FAILED: []
        }

        if target_phase not in valid_transitions.get(current, []):
            raise ValueError(f"Invalid transition: {current} -> {target_phase}")

        return {
            **state,
            "phase": target_phase.value,
            "version": state["version"] + 1,
            "updated_at": datetime.now().isoformat()
        }

    def add_agent_result(
        self,
        state: InvestmentState,
        agent_name: str,
        result: Dict[str, Any]
    ) -> InvestmentState:
        """Add agent result to state."""
        field_name = f"{agent_name}_analysis"

        return {
            **state,
            field_name: result,
            "version": state["version"] + 1,
            "updated_at": datetime.now().isoformat()
        }

    def add_error(
        self,
        state: InvestmentState,
        error: str
    ) -> InvestmentState:
        """Add error to state."""
        return {
            **state,
            "errors": state["errors"] + [error],
            "version": state["version"] + 1,
            "updated_at": datetime.now().isoformat()
        }

    def persist_state(self, state: InvestmentState) -> None:
        """Persist state if persistence layer available."""
        if self.persistence:
            self.persistence.save_state(
                state["task_id"],
                state
            )

    def load_state(self, task_id: str) -> Optional[InvestmentState]:
        """Load state from persistence."""
        if self.persistence:
            return self.persistence.load_state(task_id)
        return None

# Usage
state_manager = StateManager(
    persistence=FileStatePersistence(),
    memory=VectorMemory()
)

# Create workflow
state = state_manager.create_initial_state(
    task_id="task_123",
    stock_code="AAPL",
    user_id="user_456",
    query="Analyze Apple stock for potential investment"
)

# Transition through phases
state = state_manager.transition_phase(state, WorkflowPhase.COLLECTING)
state_manager.persist_state(state)

# Add agent results
state = state_manager.add_agent_result(
    state,
    "news",
    {"sentiment": "bullish", "confidence": 0.85}
)

state = state_manager.transition_phase(state, WorkflowPhase.ANALYZING)
state_manager.persist_state(state)
```

---

## Summary

Effective state management in multi-agent systems requires:

1. **Immutability** - Never mutate state, always return new state
2. **Minimalism** - Only include necessary data
3. **Type safety** - Use TypedDict, Pydantic, or dataclasses
4. **Explicit data flow** - Make dependencies clear
5. **Appropriate persistence** - Choose strategy based on needs
6. **Memory systems** - Implement short-term, long-term, and episodic memory
7. **Synchronization** - Handle parallel execution safely

Use these patterns as building blocks for your specific multi-agent system.
