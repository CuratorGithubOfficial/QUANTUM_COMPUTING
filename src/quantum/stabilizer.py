"""Stabilizer State — исправленная реализация."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StabilizerState:
    """Состояние стабилизатора на n кубитах."""

    n: int
    table: np.ndarray = field(default=None)

    def __post_init__(self):
        if self.table is None:
            self.table = np.zeros((2 * self.n, 2 * self.n + 1), dtype=int)
            for i in range(self.n):
                self.table[i + self.n, self.n + i] = 1  # Z_i stabilizer

    def apply_h(self, qubit: int) -> None:
        """H: X <-> Z обмен."""
        for row in range(2 * self.n):
            x = self.table[row, qubit]
            z = self.table[row, self.n + qubit]
            self.table[row, qubit] = z
            self.table[row, self.n + qubit] = x
            if x and z:
                self.table[row, 2 * self.n] ^= 1

    def apply_s(self, qubit: int) -> None:
        """S: X -> Y, Y -> -X."""
        for row in range(2 * self.n):
            x = self.table[row, qubit]
            z = self.table[row, self.n + qubit]
            if x and z:
                self.table[row, 2 * self.n] ^= 1
            if x:
                self.table[row, self.n + qubit] ^= 1

    def apply_cnot(self, control: int, target: int) -> None:
        """CNOT."""
        for row in range(2 * self.n):
            self.table[row, target] ^= self.table[row, control]
            self.table[row, self.n + control] ^= self.table[row, self.n + target]

    def apply_x(self, qubit: int) -> None:
        """X: переворот фазы Z-стабилизатора."""
        for row in range(2 * self.n):
            z = self.table[row, self.n + qubit]
            if z:
                self.table[row, 2 * self.n] ^= 1

    def apply_z(self, qubit: int) -> None:
        """Z: переворот фазы X-стабилизатора."""
        for row in range(2 * self.n):
            x = self.table[row, qubit]
            if x:
                self.table[row, 2 * self.n] ^= 1

    def measure_z(self, qubit: int) -> int:
        """Измерение в Z-базисе."""
        has_x = False
        for row in range(self.n, 2 * self.n):
            if self.table[row, qubit] == 1:
                has_x = True
                break

        if not has_x:
            result = 0
            for row in range(self.n, 2 * self.n):
                if self.table[row, self.n + qubit] == 1:
                    result = int(self.table[row, 2 * self.n])
                    break
            return result
        else:
            result = random.randint(0, 1)
            self._project_z(qubit, result)
            return result

    def _project_z(self, qubit: int, result: int) -> None:
        """Проекция после измерения."""
        for row in range(2 * self.n):
            if row != self.n + qubit:
                if self.table[row, qubit] == 1:
                    self._row_multiply(row, self.n + qubit)
                self.table[row, qubit] = 0
        self.table[self.n + qubit, 2 * self.n] = result

    def _row_multiply(self, row1: int, row2: int) -> None:
        """Умножение строк."""
        x1 = self.table[row1, 0 : self.n].copy()
        x2 = self.table[row2, 0 : self.n].copy()
        z1 = self.table[row1, self.n : 2 * self.n].copy()
        z2 = self.table[row2, self.n : 2 * self.n].copy()

        phase1 = self.table[row1, 2 * self.n]
        phase2 = self.table[row2, 2 * self.n]
        dot_product = int(np.sum(z1 & x2) % 2)
        new_phase = (phase1 + phase2 + 2 * dot_product) % 4

        self.table[row1, 0 : self.n] = x1 ^ x2
        self.table[row1, self.n : 2 * self.n] = z1 ^ z2
        self.table[row1, 2 * self.n] = new_phase
