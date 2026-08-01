
"""Утилиты для построения квантовых схем и измерений."""
import time
import logging
from typing import Dict, Optional, Tuple
from pyqpanda3.qcloud import QCloudService, QCloudOptions
from pyqpanda3.core import H, X, Z, CNOT, RX, QProg, measure

logger = logging.getLogger(__name__)

def _get_probs_safe(result) -> dict:
    """Безопасное получение вероятностей (get_probs или get_counts -> probs)."""
    try:
        probs = result.get_probs()
        if probs:
            return probs
    except Exception:
        pass
    
    try:
        counts = result.get_counts()
        if counts:
            total = sum(counts.values())
            return {k: v / total for k, v in counts.items()}
    except Exception:
        pass
    
    return {}

def create_bell_pair(prog: QProg, q0: int = 0, q1: int = 1) -> None:
    """Создает состояние Белла |Φ⁺⟩ = (|00⟩ + |11⟩)/√2."""
    prog << H(q0) << CNOT(q0, q1)

def measure_correlation(
    backend,
    theta_a: float,
    theta_b: float,
    shots: int = 2000,
    q0: int = 0,
    q1: int = 1
) -> float:
    """
    Измеряет E(a,b) = <σ_a ⊗ σ_b> для заданных углов детекторов.

    Args:
        backend: Квантовый бэкенд (QCloud).
        theta_a: Угол поворота базиса Алисы (радианы).
        theta_b: Угол поворота базиса Боба (радианы).
        shots: Количество измерений.
        q0, q1: Индексы кубитов.

    Returns:
        Коррелятор E(a,b) в диапазоне [-1, +1].
    """
    prog = QProg()
    create_bell_pair(prog, q0, q1)
    prog << RX(q0, theta_a) << RX(q1, theta_b)
    prog << measure([q0, q1], [0, 1])

    job = backend.run(prog, shots=shots, options=QCloudOptions())
    _wait_for_job(job)

    probs = _get_probs_safe(job.result())
    if not probs:
        logger.warning("No probabilities returned from backend")
        return 0.0

    expectation = 0.0
    for bs, prob in probs.items():
        bits = _parse_bitstring(str(bs), 2)
        outcome_a = +1 if bits[-2] == '0' else -1
        outcome_b = +1 if bits[-1] == '0' else -1
        expectation += outcome_a * outcome_b * prob

    return expectation


def _wait_for_job(job, poll_interval: float = 0.5, timeout: float = 300) -> None:
    """Ожидает завершения квантового задания."""
    elapsed = 0.0
    while True:
        s = str(job.status())
        if s in ("JobStatus.FINISHED", "FINISHED"):
            break
        if s in ("JobStatus.FAILED", "FAILED", "JobStatus.CANCELLED", "CANCELLED"):
            raise RuntimeError(f"Job failed with status: {s}")
        if elapsed >= timeout:
            raise TimeoutError(f"Job timed out after {timeout}s")
        time.sleep(poll_interval)
        elapsed += poll_interval


def _parse_bitstring(bs: str, n_bits: int) -> str:
    """Парсит битовую строку из hex или бинарного формата."""
    if bs.startswith('0x'):
        return format(int(bs, 16), f'0{n_bits}b')
    return bs.zfill(n_bits)


def encode_superdense(prog: QProg, bits: str, q0: int = 0, q1: int = 1) -> None:
    """
    Кодирует 2 классических бита в запутанную пару.

    Args:
        prog: Квантовая программа.
        bits: Строка из двух бит ("00", "01", "10", "11").
        q0: Кубит Алисы.
        q1: Кубит Боба.
    """
    create_bell_pair(prog, q0, q1)
    if bits == "01":
        prog << X(q0)
    elif bits == "10":
        prog << Z(q0)
    elif bits == "11":
        prog << X(q0) << Z(q0)


def decode_superdense(prog: QProg, q0: int = 0, q1: int = 1) -> None:
    """Декодирует сверхплотное кодирование (Боб)."""
    prog << CNOT(q0, q1) << H(q0)


def build_teleportation_circuit(
    state_prep_gate: str = "X",
    q_state: int = 0,
    q_alice: int = 1,
    q_bob: int = 2
) -> QProg:
    """
    Строит схему квантовой телепортации БЕЗ qif (статическая версия).

    Args:
        state_prep_gate: Гейт для подготовки состояния ("X" → |1⟩, "H" → |+⟩, "" → |0⟩).
        q_state: Кубит с телепортируемым состоянием.
        q_alice: Кубит Алисы из пары Белла.
        q_bob: Кубит Боба.

    Returns:
        QProg с измерениями всех трёх кубитов (q_bob, q_alice, q_state).
    """
    prog = QProg()

    if state_prep_gate == "X":
        prog << X(q_state)
    elif state_prep_gate == "H":
        prog << H(q_state)

    prog << H(q_alice) << CNOT(q_alice, q_bob)
    prog << CNOT(q_state, q_alice) << H(q_state)
    prog << measure([q_bob, q_alice, q_state], [0, 1, 2])

    return prog
