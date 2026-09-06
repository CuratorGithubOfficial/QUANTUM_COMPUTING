"""Abstraction Layer — интерфейсы для квантовых бэкендов.

Центральный модуль архитектуры. Определяет:
- BaseBackend — абстрактный базовый класс для всех бэкендов
- QuantumCircuit — универсальное представление схемы (не зависит от SDK)
- Реестр бэкендов через __init_subclass__

Позволяет:
- Разрабатывать пайплайны без привязки к конкретному SDK
- Подменять бэкенды (Mock для тестов, QCloud для облака)
- Регистрировать новые бэкенды автоматически
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from core.models import BackendInfo, QuantumResult

logger = logging.getLogger(__name__)


@dataclass
class QuantumCircuit:
    """Универсальное представление квантовой схемы.

    Не зависит от конкретного SDK (pyqpanda3, qiskit, cirq).
    Содержит список гейтов в нормализованном виде:
    (gate_name, qubits_tuple, params_list)
    """

    gates: list[tuple] = field(default_factory=list)

    def add_gate(
        self, name: str, qubits: tuple, params: list[float] | None = None
    ) -> QuantumCircuit:
        """Добавляет гейт в схему."""
        self.gates.append((name, qubits, params or []))
        return self

    def add_h(self, qubit: int) -> QuantumCircuit:
        return self.add_gate("H", (qubit,))

    def add_x(self, qubit: int) -> QuantumCircuit:
        return self.add_gate("X", (qubit,))

    def add_z(self, qubit: int) -> QuantumCircuit:
        return self.add_gate("Z", (qubit,))

    def add_rx(self, qubit: int, theta: float) -> QuantumCircuit:
        return self.add_gate("RX", (qubit,), [theta])

    def add_ry(self, qubit: int, theta: float) -> QuantumCircuit:
        return self.add_gate("RY", (qubit,), [theta])

    def add_rz(self, qubit: int, theta: float) -> QuantumCircuit:
        return self.add_gate("RZ", (qubit,), [theta])

    def add_cnot(self, control: int, target: int) -> QuantumCircuit:
        return self.add_gate("CNOT", (control, target))

    def __len__(self) -> int:
        return len(self.gates)

    def __repr__(self) -> str:
        return f"QuantumCircuit(gates={len(self.gates)})"


class BaseBackend(ABC):
    """Абстрактный базовый класс для всех квантовых бэкендов.

    Реализации автоматически регистрируются в _registry через __init_subclass__.
    Доступ: get_backend(name), list_backends().
    """

    _registry: ClassVar[dict[str, type[BaseBackend]]] = {}

    def __init_subclass__(cls, **kwargs):
        """Автоматическая регистрация подклассов."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "backend_name"):
            BaseBackend._registry[cls.backend_name] = cls
            logger.debug(f"Registered backend: {cls.backend_name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Имя бэкенда (например, 'mock', 'qcloud_WK_C180')."""
        ...

    @abstractmethod
    def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        options: dict[str, Any] | None = None,
    ) -> QuantumResult:
        """Запуск схемы на бэкенде.

        Args:
            circuit: универсальная схема (QuantumCircuit).
            shots: число измерений.
            options: дополнительные опции (mapping, amend, etc.).

        Returns:
            QuantumResult с counts и probabilities.
        """
        ...

    @abstractmethod
    def get_info(self) -> BackendInfo:
        """Возвращает информацию о бэкенде (калибровка, топология)."""
        ...

    def is_available(self) -> bool:
        """Проверка доступности бэкенда (по умолчанию True)."""
        return True


def get_backend(name: str, **kwargs) -> BaseBackend:
    """Фабрика бэкендов по имени.

    Args:
        name: имя бэкенда (например, 'mock', 'qcloud_WK_C180').
        **kwargs: параметры конструктора.

    Returns:
        Экземпляр BaseBackend.

    Raises:
        ValueError: если бэкенд не зарегистрирован.
    """
    if name not in BaseBackend._registry:
        available = list(BaseBackend._registry.keys())
        raise ValueError(f"Backend '{name}' not found. Available: {available}")
    return BaseBackend._registry[name](**kwargs)


def list_backends() -> list[str]:
    """Список зарегистрированных бэкендов."""
    return sorted(BaseBackend._registry.keys())


def register_backend(cls: type[BaseBackend]) -> type[BaseBackend]:
    """Декоратор для ручной регистрации бэкенда."""
    if hasattr(cls, "backend_name"):
        BaseBackend._registry[cls.backend_name] = cls
        logger.info(f"Registered backend: {cls.backend_name}")
    return cls
