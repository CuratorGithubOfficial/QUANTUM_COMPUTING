"""Тесты для утилит квантовых схем."""
import pytest
from pyqpanda3.core import CPUQVM, QProg, measure
from utils.quantum_helpers import (
    create_bell_pair,
    encode_superdense,
    decode_superdense,
    build_teleportation_circuit
)

def test_create_bell_pair():
    """Тест: создание состояния Белла на симуляторе."""
    prog = QProg()
    create_bell_pair(prog, 0, 1)
    prog << measure([0, 1], [0, 1])
    
    machine = CPUQVM()
    machine.run(prog, shots=1000)
    counts = machine.result().get_counts()
    
    has_00 = any(k in ('00', '0x0') for k in counts.keys())
    has_11 = any(k in ('11', '0x3') for k in counts.keys())
    assert has_00, f"No |00> in counts: {counts}"
    assert has_11, f"No |11> in counts: {counts}"


def test_encode_superdense_all_messages():
    """Тест: сверхплотное кодирование — все 4 сообщения декодируются однозначно."""
    results = {}
    for bits in ["00", "01", "10", "11"]:
        prog = QProg()
        encode_superdense(prog, bits, 0, 1)
        decode_superdense(prog, 0, 1)
        prog << measure([0, 1], [0, 1])
        
        machine = CPUQVM()
        machine.run(prog, shots=500)
        result = machine.result()
        counts = result.get_counts()
        
        if counts:
            # Находим доминирующий исход
            max_state = max(counts, key=counts.get)
            max_prob = counts[max_state] / sum(counts.values())
            results[bits] = (max_state, max_prob)
            
            # Каждое сообщение должно давать уникальный доминирующий исход с вероятностью > 0.9
            assert max_prob > 0.9, f"Low confidence for message {bits}: {max_prob:.4f}"
    
    # Все 4 сообщения должны давать разные доминирующие исходы
    dominant_states = [v[0] for v in results.values()]
    assert len(set(dominant_states)) == 4, f"Messages not uniquely decoded: {results}"


def test_build_teleportation_circuit():
    """Тест: схема телепортации строится без ошибок."""
    prog = build_teleportation_circuit(state_prep_gate="X")
    assert prog is not None
    
    prog2 = build_teleportation_circuit(state_prep_gate="H")
    assert prog2 is not None
    
    prog3 = build_teleportation_circuit(state_prep_gate="")
    assert prog3 is not None
