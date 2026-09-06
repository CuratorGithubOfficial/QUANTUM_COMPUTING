"""Job Queue — асинхронная очередь квантовых заданий.

Обеспечивает:
- Параллельный запуск нескольких схем с ограничением max_workers
- Exponential backoff при повторных попытках
- Сбор результатов через wait_all()

Паттерн: asyncio.Queue + ThreadPoolExecutor через run_in_executor.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from core.interfaces import BaseBackend, QuantumCircuit
from core.models import QuantumResult

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    """Результат одного задания в очереди.

    Attributes:
        job_id: уникальный идентификатор задания.
        circuit: исходная схема.
        backend_name: имя бэкенда.
        result: QuantumResult при успехе (None при отказе).
        error: сообщение об ошибке (None при успехе).
        attempts: число попыток выполнения.
        execution_time: общее время выполнения (секунды).
    """

    job_id: str
    circuit: QuantumCircuit
    backend_name: str
    result: QuantumResult | None = None
    error: str | None = None
    attempts: int = 0
    execution_time: float = 0.0


class JobQueue:
    """Асинхронная очередь заданий с exponential backoff.

    Args:
        max_workers: максимальное число параллельных заданий.
        backoff_delays: список задержек между попытками (секунды).

    Example:
        queue = JobQueue(max_workers=3)
        await queue.submit(circuit, backend, shots=1000)
        await queue.submit(circuit2, backend, shots=500)
        results = await queue.wait_all()
    """

    def __init__(
        self,
        max_workers: int = 4,
        backoff_delays: list[float] | None = None,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers должен быть >= 1")
        self._max_workers = max_workers
        self._backoff_delays = backoff_delays or [1.0, 2.0, 4.0, 8.0]
        self._queue: asyncio.Queue = asyncio.Queue()
        self._results: list[JobResult] = []
        self._workers: list[asyncio.Task] = []
        self._job_counter: int = 0

    async def submit(
        self,
        circuit: QuantumCircuit,
        backend: BaseBackend,
        shots: int,
        timeout: float | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Добавляет задание в очередь.

        Args:
            circuit: квантовая схема.
            backend: бэкенд для выполнения.
            shots: число измерений.
            timeout: таймаут выполнения (секунды, None — без таймаута).
            options: дополнительные опции для backend.run.

        Returns:
            job_id — идентификатор задания.
        """
        self._job_counter += 1
        job_id = f"job_{self._job_counter:04d}"

        await self._queue.put((job_id, circuit, backend, shots, timeout, options or {}))
        logger.info(
            "Job '%s' submitted to queue (backend='%s', shots=%d)",
            job_id,
            backend.name,
            shots,
        )
        return job_id

    async def wait_all(self) -> list[JobResult]:
        """Запускает обработку очереди и ожидает завершения всех заданий.

        Returns:
            Список JobResult в порядке завершения.
        """
        if not self._workers:
            self._start_workers()

        await self._queue.join()

        # Останавливаем воркеров
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers = []

        return self._results.copy()

    def _start_workers(self) -> None:
        """Запускает пул воркеров."""
        self._workers = [
            asyncio.create_task(self._worker(i)) for i in range(self._max_workers)
        ]

    async def _worker(self, worker_id: int) -> None:
        """Воркер: извлекает задания из очереди и выполняет их."""
        while True:
            try:
                (
                    job_id,
                    circuit,
                    backend,
                    shots,
                    timeout,
                    options,
                ) = await self._queue.get()
            except asyncio.CancelledError:
                break

            start_time = time.monotonic()
            result: QuantumResult | None = None
            error: str | None = None
            attempts = 0

            # Повторные попытки с exponential backoff
            for attempt in range(len(self._backoff_delays) + 1):
                attempts = attempt + 1
                try:
                    result = await self._run_with_timeout(
                        backend, circuit, shots, options, timeout
                    )
                    error = None
                    break
                except (RuntimeError, ValueError, TimeoutError) as exc:
                    error = str(exc)
                    if attempt < len(self._backoff_delays):
                        delay = self._backoff_delays[attempt]
                        logger.warning(
                            "Job '%s' attempt %d failed: %s. Retrying in %.1fs...",
                            job_id,
                            attempt + 1,
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)

            execution_time = time.monotonic() - start_time
            job_result = JobResult(
                job_id=job_id,
                circuit=circuit,
                backend_name=backend.name,
                result=result,
                error=error,
                attempts=attempts,
                execution_time=execution_time,
            )
            self._results.append(job_result)
            self._queue.task_done()

            if error:
                logger.error(
                    "Job '%s' failed after %d attempts: %s",
                    job_id,
                    attempts,
                    error,
                )
            else:
                logger.info(
                    "Job '%s' completed in %.2fs (attempts=%d)",
                    job_id,
                    execution_time,
                    attempts,
                )

    async def _run_with_timeout(
        self,
        backend: BaseBackend,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any],
        timeout: float | None,
    ) -> QuantumResult:
        """Запуск схемы с опциональным таймаутом."""
        loop = asyncio.get_running_loop()

        if timeout is None:
            return await loop.run_in_executor(
                None,
                lambda: backend.run(circuit, shots=shots, options=options),
            )

        return await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: backend.run(circuit, shots=shots, options=options),
            ),
            timeout=timeout,
        )
