"""Тесты для Protobuf Serializer — 4 теста."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.protobuf_serializer import ProtobufSerializer


class TestProtobufSerializer:
    """Тесты сериализатора."""

    def test_serialize_result(self):
        serializer = ProtobufSerializer()
        data = serializer.serialize_result(
            counts={"00": 500, "11": 500},
            probabilities={"00": 0.5, "11": 0.5},
            job_id="job_001",
            backend_name="mock",
        )
        assert isinstance(data, bytes)

    def test_deserialize_result(self):
        serializer = ProtobufSerializer()
        data = serializer.serialize_result(
            counts={"00": 500, "11": 500},
            job_id="job_001",
        )
        result = serializer.deserialize_result(data)
        assert result["counts"] == {"00": 500, "11": 500}
        assert result["job_id"] == "job_001"

    def test_serialize_metrics(self):
        serializer = ProtobufSerializer()
        data = serializer.serialize_metrics({"fidelity": 0.99})
        assert isinstance(data, bytes)

    def test_deserialize_metrics(self):
        serializer = ProtobufSerializer()
        data = serializer.serialize_metrics({"fidelity": 0.99})
        metrics = serializer.deserialize_metrics(data)
        assert metrics["fidelity"] == pytest.approx(0.99)
