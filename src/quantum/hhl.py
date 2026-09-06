"""HHL Algorithm — квантовое решение систем линейных уравнений.

Алгоритм Harrow-Hassidim-Lloyd для решения Ax = b:
- A — эрмитова матрица n×n
- b — известный вектор |b>
- Результат: состояние |x> = A^(-1)|b>

Этапы:
1. Quantum Phase Estimation (QPE) для собственных значений A
2. Controlled rotation (инверсия собственных значений)
3. Обратное QPE
4. Измерение вспомогательного кубита

В данной реализации:
- Матрица A = [[a, b], [b, c]] (эрмитова 2×2)
- Используется симуляция через numpy (без реального квантового бэкенда)
- Точное решение для сравнения
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HHLResult:
    """Результат HHL.

    Attributes:
        solution_vector: вектор решения |x> (нормированный).
        exact_solution: точное классическое решение.
        eigenvalues: собственные значения матрицы A.
        condition_number: число обусловленности.
        success_probability: вероятность успешного измерения.
        fidelity: точность (fidelity с точным решением).
    """

    solution_vector: np.ndarray
    exact_solution: np.ndarray
    eigenvalues: np.ndarray
    condition_number: float
    success_probability: float
    fidelity: float


class HHLSolver:
    """Решатель HHL для эрмитовых матриц 2×2.

    Args:
        matrix_a: эрмитова матрица 2×2.
        vector_b: известный вектор |b> (длина 2).
        n_clock_qubits: число кубитов для QPE (точность оценки фазы).
    """

    def __init__(
        self,
        matrix_a: np.ndarray,
        vector_b: np.ndarray,
        n_clock_qubits: int = 4,
    ) -> None:
        if matrix_a.shape != (2, 2):
            raise ValueError("Matrix A must be 2x2")
        if not np.allclose(matrix_a, matrix_a.conj().T):
            raise ValueError("Matrix A must be Hermitian")
        if len(vector_b) != 2:
            raise ValueError("Vector b must have length 2")

        self.matrix_a = matrix_a.astype(complex)
        self.vector_b = vector_b.astype(complex)
        self.n_clock_qubits = n_clock_qubits

        # Нормализация b
        norm_b = np.linalg.norm(self.vector_b)
        if norm_b == 0:
            raise ValueError("Vector b must be non-zero")
        self.normalized_b = self.vector_b / norm_b

        # Собственные значения и векторы
        self.eigenvalues, self.eigenvectors = np.linalg.eigh(self.matrix_a)
        lambda_min = min(abs(self.eigenvalues))
        lambda_max = max(abs(self.eigenvalues))
        self.condition_number = (
            lambda_max / lambda_min if lambda_min > 1e-10 else float("inf")
        )

    def solve(self) -> HHLResult:
        """Запускает HHL-алгоритм (симуляция).

        Returns:
            HHLResult с решением и метриками.
        """
        # Точное решение
        exact_x = np.linalg.solve(self.matrix_a, self.vector_b)
        exact_x_norm = exact_x / np.linalg.norm(exact_x)

        # HHL: |x> = sum_j (beta_j / lambda_j) |u_j>
        # beta_j = <u_j | b>
        solution = np.zeros(2, dtype=complex)
        for j in range(2):
            beta_j = np.dot(self.eigenvectors[:, j].conj(), self.normalized_b)
            lambda_j = self.eigenvalues[j]
            if abs(lambda_j) > 1e-10:
                solution += (beta_j / lambda_j) * self.eigenvectors[:, j]

        # Нормализация
        norm_x = np.linalg.norm(solution)
        if norm_x > 0:
            solution = solution / norm_x

        # Вероятность успеха (P(ancilla=|1>))
        # Пропорциональна ||A^(-1)|b>||^2 / ||b||^2
        numerator = np.linalg.norm(np.linalg.solve(self.matrix_a, self.normalized_b))
        success_probability = min(1.0, float(numerator**2))

        # Fidelity
        fidelity = abs(np.dot(solution.conj(), exact_x_norm)) ** 2

        return HHLResult(
            solution_vector=solution,
            exact_solution=exact_x_norm,
            eigenvalues=self.eigenvalues,
            condition_number=self.condition_number,
            success_probability=success_probability,
            fidelity=float(fidelity),
        )

    def qpe_circuit_depth(self) -> int:
        """Оценивает глубину QPE-схемы.

        Returns:
            Приблизительная глубина схемы.
        """
        # QPE глубина ~ O(n_clock_qubits^2) для 2×2 матрицы
        return self.n_clock_qubits**2
