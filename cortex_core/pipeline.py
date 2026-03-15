"""
Pipeline Orchestrator
----------------------
Runs multi-step CortexOS workflows (digest → summarise → post)
with status tracking and optional webhook notifications.
"""

from __future__ import annotations

import datetime
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    name: str
    status: StepStatus = StepStatus.PENDING
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float = 0.0
    output: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class PipelineResult:
    name: str
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    steps: list[StepResult] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_s": round(self.duration_s, 3),
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
        }


# Type alias for a pipeline step function
StepFn = Callable[..., Any]


class Pipeline:
    """Configurable, observable pipeline executor."""

    def __init__(self, name: str = "CortexOS Pipeline"):
        self.name = name
        self._steps: list[tuple[str, StepFn]] = []
        self._on_step_start: Callable[[str], None] | None = None
        self._on_step_end: Callable[[StepResult], None] | None = None

    # --------------------------------------------------------- registration

    def step(self, name: str):
        """Decorator to register a pipeline step."""

        def decorator(fn: StepFn) -> StepFn:
            self._steps.append((name, fn))
            return fn

        return decorator

    def add_step(self, name: str, fn: StepFn) -> Pipeline:
        """Imperative step registration."""
        self._steps.append((name, fn))
        return self

    # ----------------------------------------------------------- callbacks

    def on_step_start(self, callback: Callable[[str], None]) -> None:
        self._on_step_start = callback

    def on_step_end(self, callback: Callable[[StepResult], None]) -> None:
        self._on_step_end = callback

    # ------------------------------------------------------------ execution

    def run(self, *, stop_on_failure: bool = True) -> PipelineResult:
        """Execute all registered steps sequentially."""
        result = PipelineResult(
            name=self.name,
            started_at=_now(),
        )
        t0 = time.monotonic()

        for step_name, step_fn in self._steps:
            sr = StepResult(name=step_name)

            if self._on_step_start:
                self._on_step_start(step_name)

            sr.started_at = _now()
            sr.status = StepStatus.RUNNING
            step_t0 = time.monotonic()

            try:
                sr.output = step_fn()
                sr.status = StepStatus.SUCCESS
            except Exception as exc:
                sr.status = StepStatus.FAILED
                sr.error = f"{exc.__class__.__name__}: {exc}"
                result.success = False

            sr.finished_at = _now()
            sr.duration_s = round(time.monotonic() - step_t0, 3)
            result.steps.append(sr)

            if self._on_step_end:
                self._on_step_end(sr)

            if sr.status == StepStatus.FAILED and stop_on_failure:
                # Mark remaining steps as skipped
                remaining = self._steps[len(result.steps) :]
                for rname, _ in remaining:
                    result.steps.append(StepResult(name=rname, status=StepStatus.SKIPPED))
                break

        result.finished_at = _now()
        result.duration_s = round(time.monotonic() - t0, 3)
        return result

    # ----------------------------------------------------------- utilities

    @property
    def step_names(self) -> list[str]:
        return [name for name, _ in self._steps]

    def __len__(self) -> int:
        return len(self._steps)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
