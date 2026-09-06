"""In-memory хранилище заданий."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    """Запись о задании."""

    job_id: str
    status: str = "queued"
    result: dict[str, Any] | None = None
    error: str | None = None


class InMemoryJobStore:
    """Простое in-memory хранилище заданий."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create_job(self) -> str:
        """Создаёт новое задание и возвращает его ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobRecord(job_id=job_id, status="queued")
        logger.info("Job '%s' created", job_id)
        return job_id

    def update_job(
        self,
        job_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Обновляет статус задания."""
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found")
        job = self._jobs[job_id]
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        logger.info("Job '%s' updated: status=%s", job_id, status)

    def get_job(self, job_id: str) -> JobRecord:
        """Возвращает задание по ID."""
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found")
        return self._jobs[job_id]

    def delete_job(self, job_id: str) -> None:
        """Удаляет задание."""
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found")
        del self._jobs[job_id]
        logger.info("Job '%s' deleted", job_id)

    def list_jobs(self) -> dict[str, JobRecord]:
        """Возвращает все задания."""
        return self._jobs.copy()
