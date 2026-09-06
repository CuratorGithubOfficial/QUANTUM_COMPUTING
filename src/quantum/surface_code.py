"""Surface Code — топологический код коррекции ошибок.

Реализация поверхностного кода на решётке d×d:
- Data qubits — на рёбрах решётки
- X-stabilizers — на вершинах (плитки)
- Z-stabilizers — на гранях (плитки)
- Логические операторы: X_L (горизонтальная цепочка), Z_L (вертикальная цепочка)

Формат:
- Решётка (2d-1) × (2d-1), где:
  - Чётные индексы (i+j чётное) — data qubits
  - Нечётные индексы (i+j нечётное, i чётное) — X-стабилизаторы
  - Нечётные индексы (i+j нечётное, i нечётное) — Z-стабилизаторы
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SurfaceCode:
    """Поверхностный код на решётке distance × distance.

    Attributes:
        distance: кодовое расстояние d (решётка d×d).
        data_qubits: список координат data qubits.
        x_stabilizers: список координат X-стабилизаторов.
        z_stabilizers: список координат Z-стабилизаторов.
        syndrome: словарь {stabilizer_coords: eigenvalue} (текущий синдром).
    """

    distance: int
    data_qubits: list[tuple[int, int]] = field(default_factory=list)
    x_stabilizers: list[tuple[int, int]] = field(default_factory=list)
    z_stabilizers: list[tuple[int, int]] = field(default_factory=list)
    syndrome: dict[tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._build_lattice()

    def _build_lattice(self) -> None:
        """Строит решётку поверхностного кода."""
        size = 2 * self.distance - 1
        for i in range(size):
            for j in range(size):
                if (i + j) % 2 == 0:
                    self.data_qubits.append((i, j))
                else:
                    if i % 2 == 0:
                        self.x_stabilizers.append((i, j))
                    else:
                        self.z_stabilizers.append((i, j))
        logger.info(
            "Surface code built: d=%d, data_qubits=%d, X_stab=%d, Z_stab=%d",
            self.distance,
            len(self.data_qubits),
            len(self.x_stabilizers),
            len(self.z_stabilizers),
        )

    def get_x_stabilizer_qubits(
        self, stabilizer: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Возвращает data qubits, входящие в X-стабилизатор (север, юг, запад, восток)."""
        i, j = stabilizer
        neighbors = []
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if (
                0 <= ni < 2 * self.distance - 1
                and 0 <= nj < 2 * self.distance - 1
                and (ni + nj) % 2 == 0
            ):
                neighbors.append((ni, nj))
        return neighbors

    def get_z_stabilizer_qubits(
        self, stabilizer: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Возвращает data qubits, входящие в Z-стабилизатор."""
        return self.get_x_stabilizer_qubits(stabilizer)

    def measure_syndrome(
        self, error_pattern: set[tuple[int, int]]
    ) -> dict[tuple[int, int], int]:
        """Измеряет синдром для заданного паттерна ошибок.

        Args:
            error_pattern: множество координат data qubits с ошибками X.

        Returns:
            Словарь {stabilizer: eigenvalue} (-1 для детектированной ошибки).
        """
        syndrome = {}

        # X-стабилизаторы детектируют Z-ошибки
        for stab in self.x_stabilizers:
            qubits = self.get_x_stabilizer_qubits(stab)
            parity = sum(1 for q in qubits if q in error_pattern) % 2
            syndrome[stab] = -1 if parity else +1

        # Z-стабилизаторы детектируют X-ошибки (не реализовано в этой версии)
        for stab in self.z_stabilizers:
            syndrome[stab] = +1

        self.syndrome = syndrome
        return syndrome

    def get_logical_x_chain(self) -> list[tuple[int, int]]:
        """Возвращает цепочку data qubits для логического X_L (горизонтальная)."""
        chain = []
        row = 0
        for j in range(0, 2 * self.distance - 1, 2):
            if (row + j) % 2 == 0:
                chain.append((row, j))
        return chain

    def get_logical_z_chain(self) -> list[tuple[int, int]]:
        """Возвращает цепочку data qubits для логического Z_L (вертикальная)."""
        chain = []
        col = 0
        for i in range(0, 2 * self.distance - 1, 2):
            if (i + col) % 2 == 0:
                chain.append((i, col))
        return chain

    def get_num_data_qubits(self) -> int:
        """Число data qubits: d² + (d-1)²."""
        return self.distance**2 + (self.distance - 1) ** 2

    def get_num_stabilizers(self) -> int:
        """Число стабилизаторов: 2d(d-1)."""
        return len(self.x_stabilizers) + len(self.z_stabilizers)
