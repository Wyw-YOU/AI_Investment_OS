"""
State Manager for the Multi-Agent Academic Research System.

Provides:
    - AcademicResearchStateManager: manages state lifecycle,
      phase transitions, persistence, and memory
    - File-based state persistence
    - Episodic memory for tracking analysis history

Follows the multi-agent-developer skill's state management patterns:
    - Immutability: state transitions return new state objects
    - Minimalism: only necessary data in state
    - Type safety: Pydantic models with validation
    - Explicit data flow: clear dependencies between phases
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from models import (
    AcademicResearchState,
    AgentOutput,
    WorkflowPhase,
    PaperMetadata,
    QualityAssessment,
    PaperSummary,
    GapAnalysisResult,
    LiteratureReview,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File-based Persistence
# ---------------------------------------------------------------------------

class FileStatePersistence:
    """
    Persist workflow state to JSON files on disk.

    Organised by task_id with timestamped snapshots for history.
    """

    def __init__(self, base_path: str = "./state_store") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_state(
        self,
        state_id: str,
        state: AcademicResearchState,
    ) -> Path:
        """Save state to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{state_id}_{timestamp}.json"
        file_path = self.base_path / filename

        # Serialise Pydantic models
        data = state.json(indent=2)
        file_path.write_text(data, encoding="utf-8")
        logger.info("State saved to %s", file_path)
        return file_path

    def load_state(self, file_path: Path) -> Optional[AcademicResearchState]:
        """Load state from a JSON file."""
        if not file_path.exists():
            return None
        data = file_path.read_text(encoding="utf-8")
        return AcademicResearchState.parse_raw(data)

    def list_states(self, state_id: Optional[str] = None) -> list[Path]:
        """List saved state files, optionally filtered by state_id prefix."""
        if state_id:
            return sorted(self.base_path.glob(f"{state_id}_*.json"))
        return sorted(self.base_path.glob("*.json"))

    def get_latest_state(self, state_id: str) -> Optional[AcademicResearchState]:
        """Load the most recent state for a given task_id."""
        files = self.list_states(state_id)
        if not files:
            return None
        return self.load_state(files[-1])


# ---------------------------------------------------------------------------
# Episodic Memory
# ---------------------------------------------------------------------------

class EpisodicMemory:
    """
    Short-term memory for tracking recent analysis sessions.

    Stores lightweight summaries of completed analyses so that
    subsequent runs can reference prior work.
    """

    def __init__(self, max_episodes: int = 50) -> None:
        self.max_episodes = max_episodes
        self._episodes: list[dict[str, Any]] = []

    def add_episode(self, episode: dict[str, Any]) -> None:
        """Record a completed analysis episode."""
        episode["recorded_at"] = datetime.now().isoformat()
        self._episodes.append(episode)
        # Trim to max
        if len(self._episodes) > self.max_episodes:
            self._episodes = self._episodes[-self.max_episodes :]

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """Get the N most recent episodes."""
        return self._episodes[-n:]

    def get_context_string(self) -> str:
        """Format recent episodes for prompt injection."""
        if not self._episodes:
            return "No previous analyses in memory."
        parts: list[str] = []
        for ep in self._episodes[-5:]:
            ts = ep.get("recorded_at", "unknown")
            task = ep.get("task_id", "?")
            corpus_size = ep.get("corpus_size", 0)
            parts.append(f"[{ts}] Task {task} -- {corpus_size} papers analysed")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# State Manager
# ---------------------------------------------------------------------------

class AcademicResearchStateManager:
    """
    Central state management for the academic research workflow.

    Responsibilities:
        - Create initial state for a new analysis task
        - Validate and execute phase transitions (immutable)
        - Attach agent outputs to state
        - Persist state snapshots for auditability
        - Manage episodic memory for context across sessions

    Usage:
        sm = AcademicResearchStateManager(persistence=FileStatePersistence())
        state = sm.create_initial_state(task_id="t1", paper_texts=[...])
        state = sm.transition_phase(state, WorkflowPhase.EXTRACTING)
        # ... agents run ...
        state = sm.add_agent_output(state, "paper_extractor", output)
        sm.persist_state(state)
    """

    def __init__(
        self,
        persistence: Optional[FileStatePersistence] = None,
        memory: Optional[EpisodicMemory] = None,
    ) -> None:
        self.persistence = persistence
        self.memory = memory or EpisodicMemory()

    # -- State creation ------------------------------------------------------

    def create_initial_state(
        self,
        task_id: str,
        paper_texts: list[str],
        paper_filenames: Optional[list[str]] = None,
        research_question: str = "",
        session_id: str = "default",
    ) -> AcademicResearchState:
        """
        Create a fresh initial state for a new research analysis task.

        Args:
            task_id: Unique identifier for this task
            paper_texts: Raw text content of each paper
            paper_filenames: Original filenames (auto-generated if not provided)
            research_question: Optional research question to focus the analysis
            session_id: Session grouping identifier

        Returns:
            Initial AcademicResearchState in INIT phase
        """
        if not paper_filenames:
            paper_filenames = [f"paper_{i+1}.txt" for i in range(len(paper_texts))]

        state = AcademicResearchState(
            task_id=task_id,
            session_id=session_id,
            paper_texts=paper_texts,
            paper_filenames=paper_filenames,
            research_question=research_question,
            phase=WorkflowPhase.INIT,
            version=1,
        )

        logger.info(
            "Created initial state for task %s with %d papers",
            task_id,
            len(paper_texts),
        )
        return state

    # -- Phase transitions (validated, immutable) ----------------------------

    # Valid phase transitions
    _VALID_TRANSITIONS: dict[WorkflowPhase, list[WorkflowPhase]] = {
        WorkflowPhase.INIT: [WorkflowPhase.EXTRACTING, WorkflowPhase.FAILED],
        WorkflowPhase.EXTRACTING: [
            WorkflowPhase.ANALYZING_QUALITY,
            WorkflowPhase.FAILED,
        ],
        WorkflowPhase.ANALYZING_QUALITY: [
            WorkflowPhase.SUMMARIZING,
            WorkflowPhase.FAILED,
        ],
        WorkflowPhase.SUMMARIZING: [
            WorkflowPhase.IDENTIFYING_GAPS,
            WorkflowPhase.FAILED,
        ],
        WorkflowPhase.IDENTIFYING_GAPS: [
            WorkflowPhase.SYNTHESIZING,
            WorkflowPhase.FAILED,
        ],
        WorkflowPhase.SYNTHESIZING: [
            WorkflowPhase.COMPLETED,
            WorkflowPhase.FAILED,
        ],
        WorkflowPhase.COMPLETED: [],
        WorkflowPhase.FAILED: [],
    }

    def transition_phase(
        self,
        state: AcademicResearchState,
        target: WorkflowPhase,
    ) -> AcademicResearchState:
        """
        Validate and execute a phase transition.

        Returns a new state object (immutable update).
        Raises ValueError if the transition is invalid.
        """
        current = state.phase
        valid = self._VALID_TRANSITIONS.get(current, [])

        if target not in valid:
            raise ValueError(
                f"Invalid phase transition: {current.value} -> {target.value}. "
                f"Valid transitions from {current.value}: "
                f"{[v.value for v in valid]}"
            )

        new_state = state.transition_phase(target)
        logger.info(
            "Phase transition: %s -> %s (task %s, version %d)",
            current.value,
            target.value,
            state.task_id,
            new_state.version,
        )
        return new_state

    # -- Agent output management --------------------------------------------

    def add_agent_output(
        self,
        state: AcademicResearchState,
        agent_name: str,
        output: AgentOutput,
    ) -> AcademicResearchState:
        """Attach an agent output to state (immutable update)."""
        return state.add_agent_output(agent_name, output)

    def attach_extraction_results(
        self,
        state: AcademicResearchState,
        metadata_list: list[PaperMetadata],
    ) -> AcademicResearchState:
        """Attach extracted paper metadata to state."""
        return state.copy(
            update={
                "paper_metadata": metadata_list,
                "version": state.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def attach_quality_assessments(
        self,
        state: AcademicResearchState,
        assessments: list[QualityAssessment],
    ) -> AcademicResearchState:
        """Attach quality assessments to state."""
        return state.copy(
            update={
                "quality_assessments": assessments,
                "version": state.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def attach_summaries(
        self,
        state: AcademicResearchState,
        summaries: list[PaperSummary],
    ) -> AcademicResearchState:
        """Attach paper summaries to state."""
        return state.copy(
            update={
                "paper_summaries": summaries,
                "version": state.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def attach_gap_analysis(
        self,
        state: AcademicResearchState,
        gap_analysis: GapAnalysisResult,
    ) -> AcademicResearchState:
        """Attach gap analysis results to state."""
        return state.copy(
            update={
                "gap_analysis": gap_analysis,
                "version": state.version + 1,
                "updated_at": datetime.now(),
            }
        )

    def attach_literature_review(
        self,
        state: AcademicResearchState,
        review: LiteratureReview,
    ) -> AcademicResearchState:
        """Attach the final literature review to state."""
        return state.copy(
            update={
                "literature_review": review,
                "version": state.version + 1,
                "updated_at": datetime.now(),
            }
        )

    # -- Persistence ---------------------------------------------------------

    def persist_state(self, state: AcademicResearchState) -> Optional[Path]:
        """Save current state if persistence is configured."""
        if self.persistence:
            return self.persistence.save_state(state.task_id, state)
        return None

    def load_state(self, task_id: str) -> Optional[AcademicResearchState]:
        """Load most recent state for a task."""
        if self.persistence:
            return self.persistence.get_latest_state(task_id)
        return None

    # -- Memory --------------------------------------------------------------

    def record_episode(self, state: AcademicResearchState) -> None:
        """Record the current state as a completed episode in memory."""
        self.memory.add_episode({
            "task_id": state.task_id,
            "session_id": state.session_id,
            "corpus_size": len(state.paper_texts),
            "phase": state.phase.value,
            "num_agent_outputs": len(state.agent_outputs),
            "research_question": state.research_question,
        })

    def get_memory_context(self) -> str:
        """Get formatted memory context for prompt injection."""
        return self.memory.get_context_string()
