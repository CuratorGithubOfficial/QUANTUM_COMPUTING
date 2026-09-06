"""Утилиты для построения квантовых схем — версия для Abstraction Layer.

Не зависит от pyqpanda3. Работает с QuantumCircuit и BaseBackend.
В Colab оборачивает QCloudBackend, локально — MockBackend.
"""

from __future__ import annotations

import logging

from core.interfaces import BaseBackend, QuantumCircuit

logger = logging.getLogger(__name__)


def create_bell_pair(circuit: QuantumCircuit, q0: int = 0, q1: int = 1) -> None:
    """Создает состояние Белла |Φ⁺⟩ = (|00⟩ + |11⟩)/√2."""
    circuit.add_h(q0)
    circuit.add_cnot(q0, q1)


def measure_correlation(
    backend: BaseBackend,
    theta_a: float,
    theta_b: float,
    shots: int = 2000,
    q0: int = 0,
    q1: int = 1,
) -> float:
    """
    Измеряет E(a,b) = <σ_a ⊗ σ_b> для заданных углов детекторов.

    Args:
        backend: квантовый бэкенд (реализация BaseBackend).
        theta_a: угол поворота базиса Алисы (радианы).
        theta_b: угол поворота базиса Боба (радианы).
        shots: количество измерений.
        q0, q1: индексы кубитов.

    Returns:
        Коррелятор E(a,b) в диапазоне [-1, +1].
    """
    circuit = QuantumCircuit()
    create_bell_pair(circuit, q0, q1)
    circuit.add_ry(q0, theta_a)
    circuit.add_ry(q1, theta_b)

    result = backend.run(circuit, shots=shots)

    if not result.probabilities:
        logger.warning("No probabilities returned from backend")
        return 0.0

    expectation = 0.0
    for bitstring, prob in result.probabilities.items():
        bits = _parse_bitstring(bitstring, 2)
        outcome_a = +1 if bits[-2] == "0" else -1
        outcome_b = +1 if bits[-1] == "0" else -1
        expectation += outcome_a * outcome_b * prob

    return expectation


def encode_superdense(
    circuit: QuantumCircuit, bits: str, q0: int = 0, q1: int = 1
) -> None:
    """Кодирует 2 классических бита в запутанную пару."""
    create_bell_pair(circuit, q0, q1)
    if bits == "01":
        circuit.add_x(q0)
    elif bits == "10":
        circuit.add_z(q0)
    elif bits == "11":
        circuit.add_x(q0)
        circuit.add_z(q0)


def decode_superdense(circuit: QuantumCircuit, q0: int = 0, q1: int = 1) -> None:
    """Декодирует сверхплотное кодирование (Боб)."""
    circuit.add_cnot(q0, q1)
    circuit.add_h(q0)


def build_teleportation_circuit(
    state_prep_gate: str = "X",
    q_state: int = 0,
    q_alice: int = 1,
    q_bob: int = 2,
) -> QuantumCircuit:
    """
    Строит схему квантовой телепортации БЕЗ qif (статическая версия).

    Args:
        state_prep_gate: "X" → |1⟩, "H" → |+⟩, "" → |0⟩.
        q_state: кубит с телепортируемым состоянием.
        q_alice: кубит Алисы.
        q_bob: кубит Боба.

    Returns:
        QuantumCircuit с гейтами телепортации.
    """
    circuit = QuantumCircuit()

    if state_prep_gate == "X":
        circuit.add_x(q_state)
    elif state_prep_gate == "H":
        circuit.add_h(q_state)

    circuit.add_h(q_alice)
    circuit.add_cnot(q_alice, q_bob)
    circuit.add_cnot(q_state, q_alice)
    circuit.add_h(q_state)

    return circuit


def _parse_bitstring(bitstring: str, n_bits: int) -> str:
    """Парсит битовую строку из hex или бинарного формата."""
    if bitstring.startswith("0x"):
        return format(int(bitstring, 16), f"0{n_bits}b")
    return bitstring.zfill(n_bits)
