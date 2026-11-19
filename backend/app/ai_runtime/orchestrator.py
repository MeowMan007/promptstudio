"""
TSK-057: Orchestrator — state-machine based workflow runner.

Implements the five-state graph:
  PLAN → EXECUTE → HUMAN_REVIEW → APPLY → DONE
                        ↑               |
                        └───── RETRY ───┘  (on stale / schema error)

Design mirrors LangGraph's StateGraph concept so this can be dropped in
once langgraph is in the venv. Each state is a pure function:
  state_fn(state: OrchestratorState) -> OrchestratorState

The checkpointer persists snapshots so runs resume after restart.
Human-review node pauses execution; `resume(run_id, decision)` continues it.

Acceptance (TSK-057):
  - Runs resume after restart (via checkpointer).
  - Human-review node pauses and resumes on explicit decision.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# State machine nodes
# ---------------------------------------------------------------------------

class NodeName(str, Enum):
    PLAN         = "plan"
    EXECUTE      = "execute"
    HUMAN_REVIEW = "human_review"
    APPLY        = "apply"
    DONE         = "done"
    ERROR        = "error"


# ---------------------------------------------------------------------------
# Orchestrator state (the "graph state" / "checkpoint")
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorState:
    run_id: str
    project_id: str
    goal: str                               # natural-language goal / intent
    current_node: NodeName = NodeName.PLAN
    plan: list[dict[str, Any]] = field(default_factory=list)   # steps from planner
    proposals: list[dict[str, Any]] = field(default_factory=list)  # model proposals
    human_decision: str | None = None       # "approve" | "reject" | "edit"
    human_edits: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.monotonic)
    updated_at: float = field(default_factory=time.monotonic)
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_node(self, node: NodeName) -> "OrchestratorState":
        import copy
        s = copy.copy(self)
        s.current_node = node
        s.updated_at = time.monotonic()
        return s

    def checkpoint_hash(self) -> str:
        """Deterministic hash for deduplication."""
        raw = f"{self.run_id}:{self.current_node}:{len(self.proposals)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Checkpointer (in-memory; real impl uses DB / Redis)
# ---------------------------------------------------------------------------

class Checkpointer:
    """Persists OrchestratorState snapshots so runs can resume after restart."""

    def __init__(self) -> None:
        self._store: dict[str, OrchestratorState] = {}

    def save(self, state: OrchestratorState) -> None:
        self._store[state.run_id] = state

    def load(self, run_id: str) -> OrchestratorState | None:
        return self._store.get(run_id)

    def list_runs(self) -> list[str]:
        return list(self._store.keys())

    def delete(self, run_id: str) -> None:
        self._store.pop(run_id, None)


# ---------------------------------------------------------------------------
# Node implementations (pure functions)
# ---------------------------------------------------------------------------

def _node_plan(state: OrchestratorState) -> OrchestratorState:
    """
    PLAN: Break the goal into discrete field-run steps.
    Stub: returns one step per word in goal (placeholder for real planner).
    """
    words = state.goal.split()
    plan = [{"step": i, "action": w, "field_path": "body"} for i, w in enumerate(words[:5])]
    s = state.with_node(NodeName.EXECUTE)
    s.plan = plan
    return s


def _node_execute(state: OrchestratorState) -> OrchestratorState:
    """
    EXECUTE: Run each planned step (calls model_adapter in real impl).
    Stub: produces a proposal for each plan step.
    """
    proposals = [
        {"step": step["step"], "field_path": step["field_path"], "value": f"[proposal for {step['action']}]"}
        for step in state.plan
    ]
    s = state.with_node(NodeName.HUMAN_REVIEW)
    s.proposals = proposals
    return s


def _node_human_review(state: OrchestratorState) -> OrchestratorState:
    """
    HUMAN_REVIEW: Pause and wait for a human decision.
    Returns the state unchanged (paused); caller must call resume().
    """
    # This node is a pause point — returns itself to signal waiting.
    return state


def _node_apply(state: OrchestratorState) -> OrchestratorState:
    """
    APPLY: Turn approved proposals into patches and apply them.
    Stub: records result.
    """
    decision = state.human_decision or "approve"
    if decision == "reject":
        s = state.with_node(NodeName.DONE)
        s.result = {"status": "rejected", "reason": "human rejected proposals"}
        return s

    applied = state.human_edits if state.human_edits else {
        p["field_path"]: p["value"] for p in state.proposals
    }
    s = state.with_node(NodeName.DONE)
    s.result = {"status": "applied", "fields": applied, "patch_count": len(applied)}
    return s


def _node_done(state: OrchestratorState) -> OrchestratorState:
    return state


def _node_error(state: OrchestratorState) -> OrchestratorState:
    return state


# ---------------------------------------------------------------------------
# Graph transitions
# ---------------------------------------------------------------------------

_TRANSITIONS: dict[NodeName, Callable[[OrchestratorState], OrchestratorState]] = {
    NodeName.PLAN:         _node_plan,
    NodeName.EXECUTE:      _node_execute,
    NodeName.HUMAN_REVIEW: _node_human_review,
    NodeName.APPLY:        _node_apply,
    NodeName.DONE:         _node_done,
    NodeName.ERROR:        _node_error,
}

_PAUSE_NODES = {NodeName.HUMAN_REVIEW, NodeName.DONE, NodeName.ERROR}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Runs the state machine, persisting checkpoints after each node.

    Usage:
        orch = Orchestrator(checkpointer)
        state = orch.start(run_id="r1", project_id="p1", goal="write story body")
        # state is now paused at HUMAN_REVIEW
        state = orch.resume("r1", decision="approve")
        # state.current_node == NodeName.DONE
    """

    def __init__(self, checkpointer: Checkpointer | None = None) -> None:
        self._cp = checkpointer or Checkpointer()

    def start(
        self,
        *,
        run_id: str,
        project_id: str,
        goal: str,
        metadata: dict[str, Any] | None = None,
    ) -> OrchestratorState:
        """Create and run a new orchestration until the first pause point."""
        state = OrchestratorState(
            run_id=run_id,
            project_id=project_id,
            goal=goal,
            metadata=metadata or {},
        )
        return self._run(state)

    def resume(
        self,
        run_id: str,
        *,
        decision: str,
        edits: dict[str, Any] | None = None,
    ) -> OrchestratorState:
        """
        Resume a paused run from HUMAN_REVIEW with a decision.
        decision: "approve" | "reject" | "edit"
        """
        state = self._cp.load(run_id)
        if state is None:
            raise KeyError(f"No checkpoint for run_id={run_id!r}")
        if state.current_node != NodeName.HUMAN_REVIEW:
            raise RuntimeError(
                f"Run {run_id!r} is at node {state.current_node!r}, not HUMAN_REVIEW"
            )
        state = state.with_node(NodeName.APPLY)
        state.human_decision = decision
        state.human_edits = edits or {}
        return self._run(state)

    def load(self, run_id: str) -> OrchestratorState | None:
        """Load a checkpointed state (for restart after process crash)."""
        return self._cp.load(run_id)

    def _run(self, state: OrchestratorState) -> OrchestratorState:
        """Step through nodes until a pause point is reached."""
        while state.current_node not in _PAUSE_NODES:
            node_fn = _TRANSITIONS[state.current_node]
            try:
                state = node_fn(state)
            except Exception as exc:
                state = state.with_node(NodeName.ERROR)
                state.errors.append(str(exc))
                break
            self._cp.save(state)

        self._cp.save(state)
        return state
