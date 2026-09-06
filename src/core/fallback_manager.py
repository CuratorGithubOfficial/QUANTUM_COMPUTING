"""Fallback Manager — последовательный перебор бэкендов с health-check.

Обеспечивает отказоустойчивость: если основной бэкенд недоступен
или падает, автоматически переключается на резервный.

Ключевой паттерн: health-check через asyncio.wait_for + run_in_executor,
чтобы таймаут корректно прерывал блокирующие вызовы.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from core.interfaces import BaseBackend, QuantumCircuit
from core.models import QuantumResult

logger = logging.getLogger(__name__)


@dataclass
class FallbackResult:
    """Результат запуска с fallback-логикой.

    Attributes:
        success: True, если хотя бы один бэкенд выполнил схему.
        backend_name: имя успешного бэкенда (None при полном отказе).
        result: QuantumResult от успешного бэкенда (None при отказе).
        fallback_log: список записей о попытках и причинах отказа.
        error: итоговая ошибка при полном отказе (None при успехе).
    """

    success: bool
    backend_name: str | None = None
    result: QuantumResult | None = None
    fallback_log: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class FallbackManager:
    """Последовательный перебор бэкендов с проверкой доступности.

    Алгоритм:
        1. Для каждого бэкенда — health-check с таймаутом.
        2. Если доступен — запуск схемы.
        3. При успехе — возврат FallbackResult(success=True).
        4. При отказе — запись причины в fallback_log, переход к следующему.
        5. Если все отказали — FallbackResult(success=False) с error.

    Args:
        backends: список бэкендов в порядке приоритета.
        health_check_timeout: таймаут health-check в секундах (default=5.0).

    Raises:
        ValueError: если список бэкендов пуст.
    """

    def __init__(
        self,
        backends: Sequence[BaseBackend],
        health_check_timeout: float = 5.0,
    ) -> None:
        if not backends:
            raise ValueError("FallbackManager требует минимум один бэкенд")
        self._backends: list[BaseBackend] = list(backends)
        self._health_check_timeout: float = health_check_timeout

    async def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any] | None = None,
    ) -> FallbackResult:
        """Запуск схемы с последовательным fallback.

        Args:
            circuit: квантовая схема (QuantumCircuit).
            shots: число измерений.
            options: дополнительные опции для backend.run.

        Returns:
            FallbackResult с полным логом попыток.
        """
        if options is None:
            options = {}

        fallback_log: list[dict[str, Any]] = []

        for backend in self._backends:
            attempt_start: float = time.monotonic()

            # Health-check с таймаутом
            available = await self.is_backend_available(backend)
            if not available:
                fallback_log.append(
                    {
                        "backend": backend.name,
                        "attempt_time": round(time.monotonic() - attempt_start, 3),
                        "status": "unavailable",
                        "reason": "health_check_failed_or_timeout",
                    }
                )
                logger.warning("Backend '%s' unavailable, trying next...", backend.name)
                continue

            # Запуск схемы
            try:
                result: QuantumResult = await self._run_on_backend(
                    backend, circuit, shots, options
                )
                fallback_log.append(
                    {
                        "backend": backend.name,
                        "attempt_time": round(time.monotonic() - attempt_start, 3),
                        "status": "success",
                        "reason": None,
                    }
                )
                logger.info("Backend '%s' executed successfully", backend.name)
                return FallbackResult(
                    success=True,
                    backend_name=backend.name,
                    result=result,
                    fallback_log=fallback_log,
                    error=None,
                )
            except (RuntimeError, ValueError, TimeoutError) as exc:
                fallback_log.append(
                    {
                        "backend": backend.name,
                        "attempt_time": round(time.monotonic() - attempt_start, 3),
                        "status": "failed",
                        "reason": str(exc),
                    }
                )
                logger.error("Backend '%s' failed: %s", backend.name, exc)
                continue

        # Все бэкенды отказали
        error_message = (
            f"Все {len(self._backends)} бэкендов отказали. Лог: {fallback_log}"
        )
        logger.error(error_message)
        return FallbackResult(
            success=False,
            backend_name=None,
            result=None,
            fallback_log=fallback_log,
            error=error_message,
        )

    async def is_backend_available(self, backend: BaseBackend) -> bool:
        """Проверка доступности бэкенда с таймаутом.

        Критично: health-check выполняется через loop.run_in_executor,
        иначе asyncio.wait_for не сможет прервать блокирующий вызов.

        Args:
            backend: проверяемый бэкенд.

        Returns:
            True, если бэкенд ответил в пределах health_check_timeout.
        """
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, backend.is_available),
                timeout=self._health_check_timeout,
            )
            return True
        except asyncio.TimeoutError:
            return False

    async def _run_on_backend(
        self,
        backend: BaseBackend,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any],
    ) -> QuantumResult:
        """Асинхронный запуск на конкретном бэкенде."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: backend.run(circuit, shots=shots, options=options),
        )
