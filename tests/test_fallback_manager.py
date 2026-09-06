"""Тесты для FallbackManager — 7 тестов."""

import sys
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adapters.mock_adapter import MockBackend
from core.fallback_manager import FallbackManager, FallbackResult
from core.interfaces import QuantumCircuit
from core.models import QuantumResult


class FailingBackend(MockBackend):
    """Бэкенд, который всегда падает при run()."""

    def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any] | None = None,
    ) -> QuantumResult:
        self._run_calls += 1
        raise RuntimeError(f"{self._name}: run failed")


class UnavailableBackend(MockBackend):
    """Бэкенд, который не отвечает на health-check (таймаут)."""

    def is_available(self) -> bool:
        time.sleep(10.0)  # превышает таймаут
        return True


class TestFallbackManagerInit:
    """Тест 1: инициализация."""

    def test_empty_backends_raises_value_error(self):
        with pytest.raises(ValueError, match="минимум один бэкенд"):
            FallbackManager([])

    def test_non_empty_backends_ok(self):
        manager = FallbackManager([MockBackend()])
        assert len(manager._backends) == 1


class TestFallbackManagerRun:
    """Тесты 2-4: запуск с fallback-логикой."""

    @pytest.mark.asyncio
    async def test_success_on_first_backend(self):
        backend = MockBackend(name="primary", fixed_counts={"00": 500, "11": 500})
        manager = FallbackManager([backend])
        circuit = QuantumCircuit()
        circuit.add_h(0).add_cnot(0, 1)

        result = await manager.run(circuit, shots=1000)

        assert result.success is True
        assert result.backend_name == "primary"
        assert result.result is not None
        assert result.result.counts == {"00": 500, "11": 500}
        assert len(result.fallback_log) == 1
        assert result.fallback_log[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_fallback_to_second_backend(self):
        failing = FailingBackend(name="failing")
        healthy = MockBackend(name="healthy", fixed_counts={"00": 300, "11": 300})
        manager = FallbackManager([failing, healthy])
        circuit = QuantumCircuit()
        circuit.add_h(0)

        result = await manager.run(circuit, shots=600)

        assert result.success is True
        assert result.backend_name == "healthy"
        assert len(result.fallback_log) == 2
        assert result.fallback_log[0]["status"] == "failed"
        assert result.fallback_log[1]["status"] == "success"

    @pytest.mark.asyncio
    async def test_all_backends_fail(self):
        failing1 = FailingBackend(name="failing_1")
        failing2 = FailingBackend(name="failing_2")
        manager = FallbackManager([failing1, failing2])
        circuit = QuantumCircuit()
        circuit.add_h(0)

        result = await manager.run(circuit, shots=100)

        assert result.success is False
        assert result.backend_name is None
        assert result.error is not None
        assert "Все 2 бэкендов отказали" in result.error
        assert len(result.fallback_log) == 2


class TestFallbackManagerHealthCheck:
    """Тест 5: health-check с таймаутом."""

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        unavailable = UnavailableBackend(name="unavailable")
        manager = FallbackManager([unavailable], health_check_timeout=0.5)

        start = time.monotonic()
        available = await manager.is_backend_available(unavailable)
        elapsed = time.monotonic() - start

        assert available is False
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        healthy = MockBackend(name="healthy")
        manager = FallbackManager([healthy], health_check_timeout=5.0)

        available = await manager.is_backend_available(healthy)

        assert available is True


class TestFallbackResultStructure:
    """Тест 7: структура FallbackResult."""

    def test_fallback_result_dataclass(self):
        result = FallbackResult(success=True)
        assert hasattr(result, "success")
        assert hasattr(result, "backend_name")
        assert hasattr(result, "result")
        assert hasattr(result, "fallback_log")
        assert hasattr(result, "error")

    def test_fallback_result_defaults(self):
        result = FallbackResult(success=False)
        assert result.success is False
        assert result.backend_name is None
        assert result.result is None
        assert result.fallback_log == []
        assert result.error is None
