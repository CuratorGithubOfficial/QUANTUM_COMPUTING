"""Tracking — система отслеживания экспериментов.

Обеспечивает:
- ConsoleTracker — логирование в консоль и локальные артефакты
- WandbTracker — интеграция с Weights & Biases (offline-режим)
- get_tracker — фабрика трекеров

Паттерн: Strategy + Singleton (WandbTracker через __new__).
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExperimentTracker(ABC):
    """Абстрактный базовый класс для трекеров экспериментов."""

    @abstractmethod
    def init(self, project_name: str, config: dict[str, Any] | None = None) -> None:
        """Инициализация трекера.

        Args:
            project_name: имя проекта.
            config: конфигурация эксперимента.
        """
        ...

    @abstractmethod
    def log(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Логирует метрики.

        Args:
            metrics: словарь метрик (например, {"fidelity": 0.99}).
            step: номер шага (опционально).
        """
        ...

    @abstractmethod
    def log_artifact(self, file_path: Path) -> None:
        """Логирует артефакт (файл).

        Args:
            file_path: путь к файлу.
        """
        ...

    @abstractmethod
    def finish(self) -> None:
        """Завершает трекинг."""
        ...


class ConsoleTracker(ExperimentTracker):
    """Трекер с выводом в консоль и локальными артефактами.

    Args:
        artifact_dir: директория для артефактов (default: outputs/artifacts).
    """

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self._artifact_dir = artifact_dir or Path("outputs/artifacts")
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        self._project_name: str = ""
        self._start_time: float = 0.0

    def init(self, project_name: str, config: dict[str, Any] | None = None) -> None:
        """Инициализация трекера."""
        self._project_name = project_name
        self._start_time = time.time()
        logger.info("=" * 60)
        logger.info("EXPERIMENT: %s", project_name)
        if config:
            logger.info("CONFIG: %s", config)
        logger.info("=" * 60)

    def log(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Логирует метрики в консоль."""
        prefix = f"[Step {step}] " if step is not None else ""
        metrics_str = ", ".join(f"{k}={v:.6f}" for k, v in metrics.items())
        logger.info("%s%s", prefix, metrics_str)

    def log_artifact(self, file_path: Path) -> None:
        """Копирует файл в директорию артефактов."""
        import shutil

        if not file_path.exists():
            logger.warning("Artifact not found: %s", file_path)
            return
        dest = self._artifact_dir / file_path.name
        shutil.copy2(file_path, dest)
        logger.info("Artifact saved: %s", dest)

    def finish(self) -> None:
        """Завершает трекинг."""
        elapsed = time.time() - self._start_time
        logger.info("=" * 60)
        logger.info("Experiment '%s' finished in %.2fs", self._project_name, elapsed)
        logger.info("=" * 60)


class WandbTracker(ExperimentTracker):
    """Трекер для Weights & Biases (offline-режим).

    Реализует Singleton: все вызовы WandbTracker() возвращают один инстанс.
    """

    _instance: WandbTracker | None = None
    _initialized: bool = False

    def __new__(cls) -> WandbTracker:  # noqa: PYI034
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._run = None
        return cls._instance

    def init(self, project_name: str, config: dict[str, Any] | None = None) -> None:
        """Инициализация wandb в offline-режиме."""
        try:
            import wandb

            self._run = wandb.init(
                project=project_name,
                config=config or {},
                mode="offline",
            )
            self._initialized = True
            logger.info("Wandb initialized (offline): %s", project_name)
        except ImportError:
            logger.warning("wandb not installed, falling back to console")
            self._run = None

    def log(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Логирует метрики в wandb."""
        if self._run is not None:
            self._run.log(metrics, step=step)

    def log_artifact(self, file_path: Path) -> None:
        """Логирует артефакт в wandb."""
        if self._run is not None and file_path.exists():
            import wandb

            artifact = wandb.Artifact(
                name=file_path.name,
                type="artifact",
            )
            artifact.add_file(str(file_path))
            self._run.log_artifact(artifact)

    def finish(self) -> None:
        """Завершает wandb run."""
        if self._run is not None:
            self._run.finish()
            self._run = None
            self._initialized = False


def get_tracker(backend: str = "console") -> ExperimentTracker:
    """Фабрика трекеров.

    Args:
        backend: тип трекера ("console" или "wandb").

    Returns:
        Экземпляр ExperimentTracker.

    Raises:
        ValueError: если тип не поддерживается.
    """
    if backend == "console":
        return ConsoleTracker()
    elif backend == "wandb":
        return WandbTracker()
    else:
        raise ValueError(
            f"Unknown tracker backend: {backend}. Use 'console' or 'wandb'."
        )
