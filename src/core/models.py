
"""Pydantic-модели данных для квантового проекта."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class JobStatus(Enum):
    """Статусы квантового задания."""
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class QuantumResult:
    """Результат выполнения квантовой схемы."""
    counts: Dict[str, int]
    probabilities: Optional[Dict[str, float]] = None
    job_id: Optional[str] = None
    backend_name: Optional[str] = None
    execution_time: float = 0.0

@dataclass
class BellCorrelator:
    """Результат измерения одного коррелятора в тесте Белла."""
    angle_a: float
    angle_b: float
    expectation: float
    shots: int

@dataclass
class BellTestResult:
    """Полный результат теста Белла."""
    correlators: List[BellCorrelator] = field(default_factory=list)
    S_value: float = 0.0
    classical_bound: float = 2.0
    quantum_bound: float = 2.8284
    inequality_violated: bool = False

    def __post_init__(self):
        if self.correlators:
            self.S_value = sum(c.expectation for c in self.correlators[:3]) - self.correlators[3].expectation
            self.inequality_violated = self.S_value > self.classical_bound

@dataclass
class TeleportationResult:
    """Результат квантовой телепортации."""
    fidelity: float
    bob_in_target_state: float
    post_selection_rate: Optional[float] = None
    counts: Optional[Dict[str, int]] = None
    physical_qubits: Optional[List[int]] = None

@dataclass
class VQCTrainingResult:
    """Результат обучения VQC."""
    best_loss: float
    best_params: List[float]
    accuracy: float
    training_time: float
    n_iterations: int

@dataclass
class DeutschJozsaResult:
    """Результат алгоритма Дойча-Йожи."""
    probability_00: float
    is_constant: bool
    oracle_type: str
    counts: Dict[str, int]
