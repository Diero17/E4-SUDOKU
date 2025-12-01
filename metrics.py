from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Any


@dataclass
class RunMetrics:
    run_id: int
    start_time: datetime
    duration: timedelta
    board_size: int
    difficulty: str | None
    params: Any          # normalmente GeneticParams
    initial_fitness: int
    final_fitness: int
    best_fitness: int
    best_generation: int
    generations_used: int
    termination_cause: str
    fitness_history: List[int] = field(default_factory=list)


class MetricsHistory:
    def __init__(self):
        self._runs: List[RunMetrics] = []
        self._next_id: int = 1

    def add_run(self, **kwargs) -> RunMetrics:
        run = RunMetrics(run_id=self._next_id, **kwargs)
        self._runs.append(run)
        self._next_id += 1
        return run

    def list_runs(self) -> List[RunMetrics]:
        return list(self._runs)

    def clear(self) -> None:
        self._runs.clear()
        self._next_id = 1
