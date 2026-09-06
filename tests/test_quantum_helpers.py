"""Тесты для утилит квантовых схем — версия для Abstraction Layer."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adapters.mock_adapter import MockBackend
from core.interfaces import QuantumCircuit
from utils.quantum_helpers import (
    build_teleportation_circuit,
    create_bell_pair,
    decode_superdense,
    encode_superdense,
    measure_correlation,
)


def test_create_bell_pair():
    """Тест: создание состояния Белла добавляет H и CNOT."""
    circuit = QuantumCircuit()
    create_bell_pair(circuit, 0, 1)

    assert len(circuit) == 2
    assert circuit.gates[0] == ("H", (0,), [])
    assert circuit.gates[1] == ("CNOT", (0, 1), [])


def test_encode_superdense_all_messages():
    """Тест: сверхплотное кодирование — все 4 сообщения дают разные схемы."""
    circuits = {}
    for bits in ["00", "01", "10", "11"]:
        circuit = QuantumCircuit()
        encode_superdense(circuit, bits, 0, 1)
        decode_superdense(circuit, 0, 1)
        # Преобразуем params list → tuple для хэшируемости
        circuits[bits] = tuple(
            (name, qubits, tuple(params)) for name, qubits, params in circuit.gates
        )

    # Все 4 схемы должны отличаться
    unique_gates = set(circuits.values())
    assert len(unique_gates) == 4, f"Схемы не уникальны: {circuits}"


def test_build_teleportation_circuit():
    """Тест: схема телепортации строится корректно."""
    # X → |1⟩
    circuit_x = build_teleportation_circuit(state_prep_gate="X")
    assert circuit_x.gates[0] == ("X", (0,), [])
    assert ("H", (1,), []) in circuit_x.gates
    assert ("CNOT", (1, 2), []) in circuit_x.gates
    assert ("CNOT", (0, 1), []) in circuit_x.gates

    # H → |+⟩
    circuit_h = build_teleportation_circuit(state_prep_gate="H")
    assert circuit_h.gates[0] == ("H", (0,), [])

    # Пустой → |0⟩
    circuit_0 = build_teleportation_circuit(state_prep_gate="")
    assert circuit_0.gates[0] == ("H", (1,), [])


def test_measure_correlation_with_mock():
    """Тест: измерение коррелятора на MockBackend."""
    backend = MockBackend(fixed_counts={"00": 500, "11": 500})
    expectation = measure_correlation(backend, 0.0, 0.0, shots=1000)

    # Для |Φ⁺⟩ при θ_a=0, θ_b=0: E = +1
    assert abs(expectation - 1.0) < 0.01


def test_parse_bitstring():
    """Тест: парсинг битовых строк."""
    from utils.quantum_helpers import _parse_bitstring

    assert _parse_bitstring("0x3", 2) == "11"
    assert _parse_bitstring("0x0", 2) == "00"
    assert _parse_bitstring("1", 3) == "001"
    assert _parse_bitstring("101", 3) == "101"
