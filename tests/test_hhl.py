"""Тесты для HHL Algorithm — 6 тестов."""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.hhl import HHLSolver


class TestHHLInit:
    """Тесты инициализации."""

    def test_valid_matrix(self):
        """Тест: валидная эрмитова матрица."""
        A = np.array([[1.0, 0.5], [0.5, 1.0]])
        b = np.array([1.0, 0.0])
        solver = HHLSolver(A, b)
        assert solver.matrix_a.shape == (2, 2)

    def test_invalid_matrix_shape(self):
        """Тест: неверная размерность."""
        A = np.eye(3)
        b = np.array([1.0, 0.0])
        with pytest.raises(ValueError, match="2x2"):
            HHLSolver(A, b)

    def test_non_hermitian(self):
        """Тест: неэрмитова матрица."""
        A = np.array([[1.0, 0.5], [0.2, 1.0]])
        b = np.array([1.0, 0.0])
        with pytest.raises(ValueError, match="Hermitian"):
            HHLSolver(A, b)


class TestHHLSolve:
    """Тесты решения."""

    def test_solve_identity(self):
        """Тест: A = I, решение = b."""
        A = np.eye(2)
        b = np.array([1.0, 0.0])
        solver = HHLSolver(A, b)
        result = solver.solve()

        assert result.fidelity > 0.99
        assert np.allclose(result.solution_vector, [1.0, 0.0], atol=0.01)

    def test_solve_diagonal(self):
        """Тест: диагональная матрица."""
        A = np.diag([2.0, 1.0])
        b = np.array([1.0, 1.0])
        solver = HHLSolver(A, b)
        result = solver.solve()

        # Точное решение: x = [0.5, 1.0] → нормированный [0.447, 0.894]
        expected = np.array([0.5, 1.0])
        expected = expected / np.linalg.norm(expected)
        assert result.fidelity > 0.99

    def test_condition_number(self):
        """Тест: число обусловленности."""
        A = np.diag([10.0, 1.0])
        b = np.array([1.0, 0.0])
        solver = HHLSolver(A, b)
        assert solver.condition_number == pytest.approx(10.0)
