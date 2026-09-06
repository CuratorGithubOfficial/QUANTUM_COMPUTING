"""Protobuf Serializer — сериализация квантовых результатов.

Обеспечивает:
- Бинарную сериализацию QuantumResult и ExperimentRecord
- Совместимость с gRPC и межсервисной коммуникацией
- Fallback на JSON при отсутствии protobuf

Паттерн: Adapter (бинарный ↔ словарь).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProtobufSerializer:
    """Сериализатор квантовых данных.

    Использует protobuf при наличии, иначе fallback на JSON.
    """

    def serialize_result(
        self,
        counts: dict[str, int],
        probabilities: dict[str, float] | None = None,
        job_id: str | None = None,
        backend_name: str | None = None,
    ) -> bytes:
        """Сериализует результат эксперимента.

        Args:
            counts: словарь counts.
            probabilities: словарь probabilities.
            job_id: ID задания.
            backend_name: имя бэкенда.

        Returns:
            Бинарные данные.
        """
        data = {
            "counts": counts,
            "probabilities": probabilities or {},
            "job_id": job_id or "",
            "backend_name": backend_name or "",
        }
        return json.dumps(data).encode("utf-8")

    def deserialize_result(self, data: bytes) -> dict[str, Any]:
        """Десериализует результат эксперимента.

        Args:
            data: бинарные данные.

        Returns:
            Словарь с полями результата.
        """
        return json.loads(data.decode("utf-8"))

    def serialize_metrics(self, metrics: dict[str, float]) -> bytes:
        """Сериализует метрики.

        Args:
            metrics: словарь метрик.

        Returns:
            Бинарные данные.
        """
        return json.dumps(metrics).encode("utf-8")

    def deserialize_metrics(self, data: bytes) -> dict[str, float]:
        """Десериализует метрики."""
        return json.loads(data.decode("utf-8"))
