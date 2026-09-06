"""Structured Logger — JSON-логирование для квантовых экспериментов.

Обеспечивает:
- JSON-формат логов
- Контекстные поля (backend, experiment, job_id)
- Метрики в структурированном виде
- Совместимость с обычным logging

Паттерн: Decorator + Factory.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    """Структурированная запись лога.

    Attributes:
        timestamp: время в формате ISO.
        level: уровень лога.
        message: текстовое сообщение.
        experiment: имя эксперимента.
        backend: имя бэкенда.
        job_id: ID задания.
        metrics: дополнительные метрики.
    """

    timestamp: str
    level: str
    message: str
    experiment: str | None = None
    backend: str | None = None
    job_id: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Сериализует запись в JSON."""
        return json.dumps(self.__dict__, ensure_ascii=False, default=str)


class StructuredLogger:
    """Структурированный логгер.

    Args:
        name: имя логгера.
        level: уровень логирования.

    Example:
        logger = StructuredLogger("quantum.experiments")
        logger.info("Bell test started", experiment="bell_test", backend="WK_C180")
        logger.log_metrics({"fidelity": 0.996}, experiment="bell_test")
    """

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(
        self,
        level: int,
        message: str,
        experiment: str | None = None,
        backend: str | None = None,
        job_id: str | None = None,
        **metrics: Any,
    ) -> None:
        """Внутренний метод логирования."""
        entry = LogEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            level=logging.getLevelName(level),
            message=message,
            experiment=experiment,
            backend=backend,
            job_id=job_id,
            metrics=metrics,
        )
        self.logger.log(level, entry.to_json())

    def debug(
        self,
        message: str,
        experiment: str | None = None,
        **metrics: Any,
    ) -> None:
        self._log(logging.DEBUG, message, experiment=experiment, **metrics)

    def info(
        self,
        message: str,
        experiment: str | None = None,
        backend: str | None = None,
        job_id: str | None = None,
        **metrics: Any,
    ) -> None:
        self._log(
            logging.INFO,
            message,
            experiment=experiment,
            backend=backend,
            job_id=job_id,
            **metrics,
        )

    def warning(
        self,
        message: str,
        experiment: str | None = None,
        **metrics: Any,
    ) -> None:
        self._log(logging.WARNING, message, experiment=experiment, **metrics)

    def error(
        self,
        message: str,
        experiment: str | None = None,
        backend: str | None = None,
        **metrics: Any,
    ) -> None:
        self._log(
            logging.ERROR,
            message,
            experiment=experiment,
            backend=backend,
            **metrics,
        )

    def log_metrics(
        self,
        metrics: dict[str, Any],
        experiment: str | None = None,
        backend: str | None = None,
    ) -> None:
        """Логирует набор метрик."""
        self.info(
            "metrics",
            experiment=experiment,
            backend=backend,
            **metrics,
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Фабрика структурированных логгеров."""
    return StructuredLogger(name)
