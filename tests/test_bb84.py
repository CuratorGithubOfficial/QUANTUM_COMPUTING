"""Тесты для BB84 Protocol — 5 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.bb84 import BB84Protocol


class TestBB84Init:
    """Тесты инициализации."""

    def test_init(self):
        protocol = BB84Protocol(n_qubits=100, seed=42)
        assert protocol.n_qubits == 100

    def test_reproducible(self):
        """Тест: с seed результат воспроизводим."""
        p1 = BB84Protocol(n_qubits=50, seed=42)
        p2 = BB84Protocol(n_qubits=50, seed=42)
        bits1, bases1 = p1.generate_alice_bits()
        bits2, bases2 = p2.generate_alice_bits()
        assert bits1 == bits2
        assert bases1 == bases2


class TestBB84Protocol:
    """Тесты протокола."""

    def test_no_eavesdropper(self):
        """Тест: без Евы QBER = 0."""
        protocol = BB84Protocol(n_qubits=200, seed=42)
        result = protocol.run_protocol(eavesdropper=False)
        assert result.error_rate == 0.0
        assert result.key_length > 0

    def test_with_eavesdropper(self):
        """Тест: с Евой QBER > 0."""
        protocol = BB84Protocol(n_qubits=200, seed=42)
        result = protocol.run_protocol(eavesdropper=True)
        assert result.error_rate > 0.0

    def test_key_length(self):
        """Тест: длина ключа ~ n/2."""
        protocol = BB84Protocol(n_qubits=200, seed=42)
        result = protocol.run_protocol()
        assert 80 <= result.key_length <= 120  # ~100 ± 20
