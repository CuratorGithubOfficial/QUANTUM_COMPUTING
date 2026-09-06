"""Тесты для Surface Code — 6 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.surface_code import SurfaceCode


class TestSurfaceCodeInit:
    """Тесты инициализации."""

    def test_distance_2_lattice(self):
        """Тест: решётка d=2."""
        sc = SurfaceCode(distance=2)
        assert sc.distance == 2
        assert len(sc.data_qubits) == 5  # 4 + 1
        assert len(sc.x_stabilizers) == 2
        assert len(sc.z_stabilizers) == 2

    def test_distance_3_lattice(self):
        """Тест: решётка d=3."""
        sc = SurfaceCode(distance=3)
        assert len(sc.data_qubits) == 13  # 9 + 4
        assert len(sc.x_stabilizers) == 6
        assert len(sc.z_stabilizers) == 6


class TestSurfaceCodeStabilizers:
    """Тесты стабилизаторов."""

    def test_x_stabilizer_neighbors(self):
        """Тест: X-стабилизатор имеет 4 соседа (внутренний)."""
        sc = SurfaceCode(distance=3)
        stab = (2, 1)  # X-стабилизатор (внутренний, 4 соседа)
        neighbors = sc.get_x_stabilizer_qubits(stab)
        assert len(neighbors) == 4

    def test_z_stabilizer_neighbors(self):
        """Тест: Z-стабилизатор имеет 4 соседа."""
        sc = SurfaceCode(distance=3)
        stab = (1, 2)  # Z-стабилизатор (внутренний, 4 соседа)
        neighbors = sc.get_z_stabilizer_qubits(stab)
        assert len(neighbors) == 4


class TestSurfaceCodeSyndrome:
    """Тесты синдромов."""

    def test_single_error_detection(self):
        """Тест: одиночная ошибка детектируется."""
        sc = SurfaceCode(distance=3)
        error = {(0, 0)}  # ошибка на data qubit
        syndrome = sc.measure_syndrome(error)
        assert any(v == -1 for v in syndrome.values())

    def test_no_error(self):
        """Тест: без ошибок синдром пустой."""
        sc = SurfaceCode(distance=3)
        syndrome = sc.measure_syndrome(set())
        assert all(v == +1 for v in syndrome.values())


class TestLogicalOperators:
    """Тесты логических операторов."""

    def test_logical_x_chain(self):
        """Тест: цепочка X_L имеет длину d."""
        sc = SurfaceCode(distance=3)
        chain = sc.get_logical_x_chain()
        assert len(chain) == 3

    def test_logical_z_chain(self):
        """Тест: цепочка Z_L имеет длину d."""
        sc = SurfaceCode(distance=3)
        chain = sc.get_logical_z_chain()
        assert len(chain) == 3
