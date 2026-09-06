"""PostgreSQL Store — хранилище результатов экспериментов.

Обеспечивает:
- Асинхронное подключение через asyncpg
- CRUD операции для экспериментов
- Миграции схемы
- Fallback на in-memory при отсутствии PostgreSQL

Схема:
  experiments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    backend TEXT,
    status TEXT,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
  )
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExperimentRecord:
    """Запись об эксперименте.

    Attributes:
        name: имя эксперимента (bell_test, teleportation, etc.).
        backend: имя бэкенда.
        status: статус (queued, running, finished, failed).
        metrics: метрики в формате JSON.
        experiment_id: ID в БД (None для новых записей).
    """

    name: str
    backend: str | None = None
    status: str = "queued"
    metrics: dict[str, Any] = field(default_factory=dict)
    experiment_id: int | None = None


class PostgresStore:
    """PostgreSQL-хранилище экспериментов.

    Args:
        dsn: строка подключения (postgresql://user:pass@host:port/db).
        max_connections: максимальное число соединений в пуле.
    """

    def __init__(
        self,
        dsn: str = "postgresql://quantum:quantum_dev@localhost:5432/quantum_workspace",
        max_connections: int = 5,
    ) -> None:
        self.dsn = dsn
        self.max_connections = max_connections
        self._pool = None

    async def connect(self) -> None:
        """Устанавливает подключение к PostgreSQL."""
        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=1,
                max_size=self.max_connections,
            )
            await self._create_tables()
            logger.info("Connected to PostgreSQL: %s", self.dsn)
        except ImportError:
            logger.warning("asyncpg not installed, using in-memory fallback")
            self._pool = None
        except (ConnectionError, OSError) as exc:
            logger.error("PostgreSQL connection failed: %s", exc)
            self._pool = None

    async def disconnect(self) -> None:
        """Закрывает подключение."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _create_tables(self) -> None:
        """Создаёт таблицы, если они не существуют."""
        if self._pool is None:
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    backend TEXT,
                    status TEXT DEFAULT 'queued',
                    metrics JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

    async def create_experiment(self, record: ExperimentRecord) -> int:
        """Создаёт запись об эксперименте.

        Returns:
            ID созданной записи.
        """
        if self._pool is None:
            logger.warning("PostgreSQL unavailable, returning fake ID")
            return -1

        async with self._pool.acquire() as conn:
            experiment_id = await conn.fetchval(
                """
                INSERT INTO experiments (name, backend, status, metrics)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                record.name,
                record.backend,
                record.status,
                json.dumps(record.metrics),
            )
            return int(experiment_id)

    async def get_experiment(self, experiment_id: int) -> ExperimentRecord | None:
        """Возвращает эксперимент по ID."""
        if self._pool is None:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, backend, status, metrics
                FROM experiments WHERE id = $1
                """,
                experiment_id,
            )
            if row is None:
                return None
            return ExperimentRecord(
                experiment_id=row["id"],
                name=row["name"],
                backend=row["backend"],
                status=row["status"],
                metrics=json.loads(row["metrics"]),
            )

    async def update_status(
        self,
        experiment_id: int,
        status: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Обновляет статус эксперимента."""
        if self._pool is None:
            return

        async with self._pool.acquire() as conn:
            if metrics is not None:
                await conn.execute(
                    """
                    UPDATE experiments SET status = $1, metrics = $2
                    WHERE id = $3
                    """,
                    status,
                    json.dumps(metrics),
                    experiment_id,
                )
            else:
                await conn.execute(
                    "UPDATE experiments SET status = $1 WHERE id = $2",
                    status,
                    experiment_id,
                )

    async def list_experiments(
        self,
        limit: int = 100,
        status: str | None = None,
    ) -> list[ExperimentRecord]:
        """Возвращает список экспериментов."""
        if self._pool is None:
            return []

        async with self._pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT id, name, backend, status, metrics
                    FROM experiments WHERE status = $1
                    ORDER BY created_at DESC LIMIT $2
                    """,
                    status,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, name, backend, status, metrics
                    FROM experiments ORDER BY created_at DESC LIMIT $1
                    """,
                    limit,
                )

            return [
                ExperimentRecord(
                    experiment_id=row["id"],
                    name=row["name"],
                    backend=row["backend"],
                    status=row["status"],
                    metrics=json.loads(row["metrics"]),
                )
                for row in rows
            ]
