"""Тесты для PostgreSQL Store — 5 тестов (fallback-режим)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.postgres_store import ExperimentRecord, PostgresStore


class TestExperimentRecord:
    """Тесты структуры записи."""

    def test_default_record(self):
        record = ExperimentRecord(name="bell_test")
        assert record.name == "bell_test"
        assert record.status == "queued"
        assert record.metrics == {}
        assert record.experiment_id is None

    def test_record_with_metrics(self):
        record = ExperimentRecord(
            name="teleportation",
            backend="WK_C180",
            metrics={"fidelity": 0.99},
        )
        assert record.backend == "WK_C180"
        assert record.metrics["fidelity"] == 0.99


class TestPostgresStoreFallback:
    """Тесты fallback-режима (без PostgreSQL)."""

    @pytest.mark.asyncio
    async def test_connect_fallback(self):
        store = PostgresStore()
        await store.connect()
        assert store._pool is None

    @pytest.mark.asyncio
    async def test_create_experiment_fallback(self):
        store = PostgresStore()
        await store.connect()
        record = ExperimentRecord(name="bell_test")
        experiment_id = await store.create_experiment(record)
        assert experiment_id == -1

    @pytest.mark.asyncio
    async def test_get_experiment_fallback(self):
        store = PostgresStore()
        await store.connect()
        result = await store.get_experiment(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_experiments_fallback(self):
        store = PostgresStore()
        await store.connect()
        experiments = await store.list_experiments()
        assert experiments == []
