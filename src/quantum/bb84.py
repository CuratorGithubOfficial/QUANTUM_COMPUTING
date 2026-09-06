"""BB84 Protocol — квантовое распределение ключей.

Протокол BB84 (Bennett-Brassard 1984):
- Алиса генерирует случайные биты и базисы (Z или X)
- Боб измеряет в случайных базисах
- Алиса и Боб сверяют базисы по открытому каналу
- Биты с совпавшими базисами формируют ключ
- Присутствие Евы детектируется по ошибкам

Базисы:
- Z: |0>, |1> (стандартный)
- X: |+> = (|0>+|1>)/√2, |-> = (|0>-|1>)/√2 (диагональный)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BB84Result:
    """Результат BB84.

    Attributes:
        alice_bits: биты Алисы.
        alice_bases: базисы Алисы (0=Z, 1=X).
        bob_bases: базисы Боба.
        bob_bits: биты Боба (после измерения).
        matching_indices: индексы с совпавшими базисами.
        raw_key: сырой ключ (биты с совпавшими базисами).
        error_rate: частота ошибок (QBER).
        key_length: длина финального ключа.
    """

    alice_bits: list[int]
    alice_bases: list[int]
    bob_bases: list[int]
    bob_bits: list[int]
    matching_indices: list[int] = field(default_factory=list)
    raw_key: list[int] = field(default_factory=list)
    error_rate: float = 0.0
    key_length: int = 0


class BB84Protocol:
    """Реализация протокола BB84.

    Args:
        n_qubits: число кубитов для передачи.
        seed: seed для воспроизводимости.
    """

    def __init__(self, n_qubits: int = 100, seed: int | None = None) -> None:
        self.n_qubits = n_qubits
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate_alice_bits(self) -> tuple[list[int], list[int]]:
        """Алиса генерирует случайные биты и базисы."""
        if self.seed is not None:
            random.seed(self.seed)
        bits = [random.randint(0, 1) for _ in range(self.n_qubits)]
        bases = [random.randint(0, 1) for _ in range(self.n_qubits)]
        return bits, bases

    def generate_bob_bases(self) -> list[int]:
        """Боб генерирует случайные базисы."""
        return [random.randint(0, 1) for _ in range(self.n_qubits)]

    def measure_bob(
        self,
        alice_bits: list[int],
        alice_bases: list[int],
        bob_bases: list[int],
        eavesdropper: bool = False,
    ) -> list[int]:
        """Боб измеряет кубиты.

        Args:
            alice_bits: биты Алисы.
            alice_bases: базисы Алисы.
            bob_bases: базисы Боба.
            eavesdropper: если True — Ева вмешивается (вносит ошибки).

        Returns:
            Биты Боба.
        """
        bob_bits = []
        for i in range(self.n_qubits):
            if alice_bases[i] == bob_bases[i]:
                # Базисы совпали — бит передаётся без ошибок (без Евы)
                if eavesdropper and random.random() < 0.5:
                    bob_bits.append(1 - alice_bits[i])  # Ева вносит ошибку
                else:
                    bob_bits.append(alice_bits[i])
            else:
                # Базисы не совпали — случайный результат
                bob_bits.append(random.randint(0, 1))
        return bob_bits

    def sift_key(
        self,
        alice_bits: list[int],
        alice_bases: list[int],
        bob_bits: list[int],
        bob_bases: list[int],
    ) -> BB84Result:
        """Сверяет базисы и формирует ключ.

        Returns:
            BB84Result с сырым ключом и метриками.
        """
        matching_indices = []
        raw_key = []

        for i in range(self.n_qubits):
            if alice_bases[i] == bob_bases[i]:
                matching_indices.append(i)
                raw_key.append(alice_bits[i])

        # Ошибки (для eavesdropper-detection)
        errors = 0
        for idx in matching_indices:
            if alice_bits[idx] != bob_bits[idx]:
                errors += 1

        error_rate = errors / len(matching_indices) if matching_indices else 0.0

        return BB84Result(
            alice_bits=alice_bits,
            alice_bases=alice_bases,
            bob_bases=bob_bases,
            bob_bits=bob_bits,
            matching_indices=matching_indices,
            raw_key=raw_key,
            error_rate=error_rate,
            key_length=len(raw_key),
        )

    def run_protocol(self, eavesdropper: bool = False) -> BB84Result:
        """Запускает полный протокол BB84.

        Args:
            eavesdropper: если True — Ева присутствует.

        Returns:
            BB84Result с результатами.
        """
        alice_bits, alice_bases = self.generate_alice_bits()
        bob_bases = self.generate_bob_bases()
        bob_bits = self.measure_bob(
            alice_bits,
            alice_bases,
            bob_bases,
            eavesdropper=eavesdropper,
        )
        return self.sift_key(alice_bits, alice_bases, bob_bits, bob_bases)
