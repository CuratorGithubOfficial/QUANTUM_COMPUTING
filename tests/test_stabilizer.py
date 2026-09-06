"""Тесты для StabilizerState — 6 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.stabilizer import StabilizerState


class TestStabilizerInit:
    """Тесты инициализации."""

    def test_init_zero_state(self):
        """Тест: |00> состояние."""
        s = StabilizerState(n=2)
        assert s.n == 2
        assert s.table.shape == (4, 5)

    def test_init_single_qubit(self):
        """Тест: |0> состояние."""
        s = StabilizerState(n=1)
        assert s.table[1, 1] == 1  # Z stabilizer (column 1 = Z)
        assert s.table[1, 2] == 0  # phase +1


class TestStabilizerGates:
    """Тесты гейтов."""

    def test_h_gate(self):
        """Тест: H|0> = |+>."""
        s = StabilizerState(n=1)
        s.apply_h(0)
        # После H: X stabilizer
        assert s.table[1, 0] == 1
        assert s.table[1, 1] == 0

    def test_x_gate(self):
        """Тест: X|0> = |1>."""
        s = StabilizerState(n=1)
        s.apply_x(0)
        # После X: Z stabilizer с фазой -1
        assert s.table[1, 1] == 1
        assert s.table[1, 2] == 1

    def test_cnot_bell(self):
        """Тест: CNOT создаёт состояние Белла."""
        s = StabilizerState(n=2)
        s.apply_h(0)
        s.apply_cnot(0, 1)
        # Проверяем, что таблица валидна (нет ошибок)
        assert s.table.shape == (4, 5)


class TestStabilizerMeasurement:
    """Тесты измерений."""

    def test_measure_deterministic(self):
        """Тест: измерение |0> даёт 0."""
        s = StabilizerState(n=1)
        result = s.measure_z(0)
        assert result == 0

    def test_measure_random(self):
        """Тест: измерение |+> даёт 0 или 1."""
        s = StabilizerState(n=1)
        s.apply_h(0)
        results = set()
        for _ in range(20):
            s2 = StabilizerState(n=1)
            s2.apply_h(0)
            results.add(s2.measure_z(0))
        assert results == {0, 1}
