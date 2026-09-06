"""Mock-адаптер для локального тестирования без pyqpanda3.

Реализует BaseBackend. Не эмулирует квантовые вычисления,
а возвращает предопределённые результаты (fixed_counts).
Используется для:
- Тестирования пайплайнов без облака
- CI/CD (не требует pyqpanda3)
- Разработки Abstraction Layer

В Colab заменяется на QCloudBackend (реальные чипы).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.interfaces import BaseBackend, QuantumCircuit
from core.models import BackendInfo, QuantumResult

logger = logging.getLogger(__name__)


class MockBackend(BaseBackend):
    """Mock-бэкенд с предопределёнными результатами.

    Args:
        name: имя бэкенда (по умолчанию 'mock').
        fixed_counts: предопределённые counts (например, {'00': 500, '11': 500}).
        fidelity_1q: точность однокубитных гейтов (для get_info).
        fidelity_2q: точность двухкубитных гейтов.
        delay: задержка в секундах (эмуляция сетевой задержки).
    """

    backend_name = "mock"

    def __init__(
        self,
        name: str = "mock",
        fixed_counts: dict[str, int] | None = None,
        fidelity_1q: float = 0.999,
        fidelity_2q: float = 0.97,
        delay: float = 0.0,
    ) -> None:
        self._name = name
        self._fixed_counts = fixed_counts or {"00": 500, "11": 500}
        self._fidelity_1q = fidelity_1q
        self._fidelity_2q = fidelity_2q
        self._delay = delay
        self._run_calls: int = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def run_calls(self) -> int:
        """Число вызовов run() — для тестирования."""
        return self._run_calls

    def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any] | None = None,
    ) -> QuantumResult:
        """Запуск схемы — возвращает масштабированные fixed_counts."""
        self._run_calls += 1

        if self._delay > 0:
            time.sleep(self._delay)

        # Масштабируем counts под shots
        total_fixed = sum(self._fixed_counts.values())
        if total_fixed == 0:
            scaled_counts = {}
            probabilities = {}
        else:
            scaled_counts = {
                k: int(v * shots / total_fixed) for k, v in self._fixed_counts.items()
            }
            # Корректировка округления
            diff = shots - sum(scaled_counts.values())
            if diff > 0 and scaled_counts:
                first_key = next(iter(scaled_counts))
                scaled_counts[first_key] += diff
            probabilities = {k: v / shots for k, v in scaled_counts.items()}

        return QuantumResult(
            counts=scaled_counts,
            probabilities=probabilities,
            job_id=f"mock_job_{self._run_calls:04d}",
            backend_name=self._name,
            execution_time=0.01 + self._delay,
        )

    def get_info(self) -> BackendInfo:
        """Информация о mock-бэкенде."""
        return BackendInfo(
            name=self._name,
            num_qubits=2,
            basis_gates=["h", "x", "z", "rx", "ry", "rz", "cx"],
            fidelity_1q=self._fidelity_1q,
            fidelity_2q=self._fidelity_2q,
            t1=100e-6,
            t2=80e-6,
            extra={"type": "mock", "description": "Предопределённые результаты"},
        )

    def is_available(self) -> bool:
        """Mock всегда доступен."""
        return True
