"""Тесты для Structured Logger — 5 тестов."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.structured_logger import (
    LogEntry,
    StructuredLogger,
    get_structured_logger,
)


class TestLogEntry:
    """Тесты структуры записи."""

    def test_log_entry_json(self):
        entry = LogEntry(
            timestamp="2026-09-06T12:00:00",
            level="INFO",
            message="test",
            experiment="bell_test",
        )
        json_str = entry.to_json()
        data = json.loads(json_str)
        assert data["message"] == "test"
        assert data["experiment"] == "bell_test"


class TestStructuredLogger:
    """Тесты логгера."""

    def test_info_with_context(self, caplog):
        import logging

        caplog.set_level(logging.INFO)
        logger = StructuredLogger("test.logger")
        logger.info(
            "Bell test started",
            experiment="bell_test",
            backend="WK_C180",
            job_id="job_001",
        )
        assert "bell_test" in caplog.text
        assert "WK_C180" in caplog.text

    def test_log_metrics(self, caplog):
        import logging

        caplog.set_level(logging.INFO)
        logger = StructuredLogger("test.logger")
        logger.log_metrics(
            {"fidelity": 0.996, "shots": 2000},
            experiment="bell_test",
        )
        assert "fidelity" in caplog.text
        assert "0.996" in caplog.text


class TestFactory:
    """Тесты фабрики."""

    def test_get_structured_logger(self):
        logger = get_structured_logger("test.factory")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test.factory"
