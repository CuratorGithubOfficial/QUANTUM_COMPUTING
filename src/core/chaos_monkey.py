"""Quantum Chaos Monkey — тестирование отказоустойчивости.

Намеренно вносит случайные сбои в систему для проверки устойчивости:
- Случайные отказы бэкендов
- Задержки
- Потеря пакетов
- Падение воркеров

Паттерн: Fault Injection.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChaosConfig:
    """Конфигурация Chaos Monkey.

    Attributes:
        failure_rate: вероятность отказа (0.0 - 1.0).
        delay_rate: вероятность задержки.
        max_delay: максимальная задержка (секунды).
        seed: seed для воспроизводимости.
    """

    failure_rate: float = 0.1
    delay_rate: float = 0.1
    max_delay: float = 1.0
    seed: int | None = None


@dataclass
class ChaosResult:
    """Результат внедрения хаоса.

    Attributes:
        chaos_applied: был ли применён хаос.
        chaos_type: тип хаоса ("failure", "delay", "none").
        original_result: оригинальный результат (до хаоса).
        chaos_result: результат после хаоса (None при failure).
    """

    chaos_applied: bool
    chaos_type: str
    original_result: Any | None = None
    chaos_result: Any | None = None


class QuantumChaosMonkey:
    """Внедрение хаоса в квантовые операции.

    Args:
        config: конфигурация хаоса.
    """

    def __init__(self, config: ChaosConfig | None = None) -> None:
        self.config = config or ChaosConfig()
        if self.config.seed is not None:
            random.seed(self.config.seed)

    def apply_chaos(
        self,
        operation: Any,
        *args: Any,
        **kwargs: Any,
    ) -> ChaosResult:
        """Применяет хаос к операции.

        Args:
            operation: функция для вызова.
            *args: аргументы функции.
            **kwargs: ключевые аргументы.

        Returns:
            ChaosResult с информацией о применённом хаосе.
        """
        # 1. Случайный отказ
        if random.random() < self.config.failure_rate:
            logger.warning("Chaos Monkey: injecting failure")
            return ChaosResult(
                chaos_applied=True,
                chaos_type="failure",
                original_result=None,
                chaos_result=None,
            )

        # 2. Случайная задержка
        if random.random() < self.config.delay_rate:
            delay = random.uniform(0, self.config.max_delay)
            logger.info("Chaos Monkey: injecting delay %.2fs", delay)
            time.sleep(delay)
            result = operation(*args, **kwargs)
            return ChaosResult(
                chaos_applied=True,
                chaos_type="delay",
                original_result=result,
                chaos_result=result,
            )

        # 3. Без хаоса
        result = operation(*args, **kwargs)
        return ChaosResult(
            chaos_applied=False,
            chaos_type="none",
            original_result=result,
            chaos_result=result,
        )

    def run_chaos_test(
        self,
        operation: Any,
        n_iterations: int = 10,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, int]:
        """Запускает серию тестов с хаосом.

        Args:
            operation: функция для вызова.
            n_iterations: число итераций.
            *args, **kwargs: аргументы функции.

        Returns:
            Статистика: {"total": N, "failures": X, "delays": Y, "successes": Z}.
        """
        stats = {"total": n_iterations, "failures": 0, "delays": 0, "successes": 0}

        for i in range(n_iterations):
            result = self.apply_chaos(operation, *args, **kwargs)
            if result.chaos_type == "failure":
                stats["failures"] += 1
            elif result.chaos_type == "delay":
                stats["delays"] += 1
                stats["successes"] += 1
            else:
                stats["successes"] += 1

        logger.info("Chaos test results: %s", stats)
        return stats
