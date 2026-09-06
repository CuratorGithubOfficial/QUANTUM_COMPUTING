"""Тесты для JobQueue — 6 тестов."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from adapters.mock_adapter import MockBackend
from core.interfaces import QuantumCircuit
from core.job_queue import JobQueue, JobResult


class TestJobQueueInit:
    """Тест 1: инициализация."""

    def test_invalid_max_workers(self):
        with pytest.raises(ValueError, match="max_workers"):
            JobQueue(max_workers=0)

    def test_valid_init(self):
        queue = JobQueue(max_workers=2)
        assert queue._max_workers == 2
        assert queue._backoff_delays == [1.0, 2.0, 4.0, 8.0]


class TestJobQueueSubmit:
    """Тест 2: отправка заданий."""

    @pytest.mark.asyncio
    async def test_submit_returns_job_id(self):
        queue = JobQueue()
        backend = MockBackend()
        circuit = QuantumCircuit()
        circuit.add_h(0)

        job_id = await queue.submit(circuit, backend, shots=100)

        assert job_id == "job_0001"

    @pytest.mark.asyncio
    async def test_submit_multiple_jobs(self):
        queue = JobQueue()
        backend = MockBackend()
        circuit = QuantumCircuit()
        circuit.add_h(0)

        id1 = await queue.submit(circuit, backend, shots=100)
        id2 = await queue.submit(circuit, backend, shots=200)

        assert id1 == "job_0001"
        assert id2 == "job_0002"


class TestJobQueueExecution:
    """Тесты 3-5: выполнение заданий."""

    @pytest.mark.asyncio
    async def test_single_job_execution(self):
        queue = JobQueue(max_workers=2)
        backend = MockBackend(fixed_counts={"00": 500, "11": 500})
        circuit = QuantumCircuit()
        circuit.add_h(0).add_cnot(0, 1)

        await queue.submit(circuit, backend, shots=1000)
        results = await queue.wait_all()

        assert len(results) == 1
        assert results[0].error is None
        assert results[0].result is not None
        assert results[0].result.counts == {"00": 500, "11": 500}
        assert results[0].attempts == 1

    @pytest.mark.asyncio
    async def test_multiple_jobs_parallel(self):
        queue = JobQueue(max_workers=3)
        backend = MockBackend(delay=0.01)
        circuit = QuantumCircuit()
        circuit.add_h(0)

        for i in range(5):
            await queue.submit(circuit, backend, shots=100)

        results = await queue.wait_all()

        assert len(results) == 5
        assert all(r.error is None for r in results)

    @pytest.mark.asyncio
    async def test_failing_job_with_retries(self):
        from adapters.mock_adapter import MockBackend

        class FailingOnceBackend(MockBackend):
            def __init__(self):
                super().__init__()
                self.fail_count = 1
                self.actual_run_calls = 0

            def run(self, circuit, shots, options=None):
                self.actual_run_calls += 1
                if self.fail_count > 0:
                    self.fail_count -= 1
                    raise RuntimeError("first attempt fails")
                return super().run(circuit, shots, options)

        queue = JobQueue(max_workers=1, backoff_delays=[0.01, 0.02])
        backend = FailingOnceBackend()
        circuit = QuantumCircuit()
        circuit.add_h(0)

        await queue.submit(circuit, backend, shots=100)
        results = await queue.wait_all()

        assert len(results) == 1
        assert results[0].error is None
        assert results[0].attempts == 2
        assert backend.actual_run_calls == 2


class TestJobResultStructure:
    """Тест 6: структура JobResult."""

    def test_job_result_fields(self):
        circuit = QuantumCircuit()
        result = JobResult(
            job_id="test",
            circuit=circuit,
            backend_name="mock",
        )
        assert result.job_id == "test"
        assert result.backend_name == "mock"
        assert result.result is None
        assert result.error is None
        assert result.attempts == 0
        assert result.execution_time == 0.0
