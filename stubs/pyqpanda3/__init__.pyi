"""Type stubs for pyqpanda3 — минимальный интерфейс для mypy."""

from .core import CNOT, CPUQVM, RX, RY, RZ, H, QProg, X, Z, measure
from .qcloud import QCloudOptions, QCloudService

__all__ = [
    "CNOT",
    "CPUQVM",
    "RX",
    "RY",
    "RZ",
    "H",
    "QCloudOptions",
    "QCloudService",
    "QProg",
    "X",
    "Z",
    "measure",
]
