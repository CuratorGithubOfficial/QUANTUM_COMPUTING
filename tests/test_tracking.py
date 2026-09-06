"""Тесты для Tracking — 5 тестов."""

import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from utils.tracking import ConsoleTracker, WandbTracker, get_tracker


@pytest.fixture(autouse=True)
def setup_logging():
    """Настройка root logger для тестов."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    yield
    root.handlers.clear()


class TestConsoleTracker:
    """Тесты ConsoleTracker."""

    def test_init(self, tmp_path):
        tracker = ConsoleTracker(artifact_dir=tmp_path)
        tracker.init("test_experiment", {"shots": 1000})
        assert tracker._project_name == "test_experiment"

    def test_log(self, caplog):
        caplog.set_level(logging.INFO)
        tracker = ConsoleTracker()
        tracker.init("test")
        tracker.log({"fidelity": 0.99})
        assert "fidelity=0.990000" in caplog.text

    def test_finish(self, caplog):
        caplog.set_level(logging.INFO)
        tracker = ConsoleTracker()
        tracker.init("test")
        tracker.finish()
        assert "finished" in caplog.text


class TestWandbTracker:
    """Тесты WandbTracker."""

    def test_singleton(self):
        tracker1 = WandbTracker()
        tracker2 = WandbTracker()
        assert tracker1 is tracker2


class TestGetTracker:
    """Тесты фабрики трекеров."""

    def test_console(self):
        tracker = get_tracker("console")
        assert isinstance(tracker, ConsoleTracker)

    def test_wandb(self):
        tracker = get_tracker("wandb")
        assert isinstance(tracker, WandbTracker)

    def test_invalid(self):
        with pytest.raises(ValueError, match="Unknown tracker"):
            get_tracker("invalid")
