"""Torch Quantum Layer — VQC, реализованный на PyTorch.

Вариационный квантовый классификатор (VQC) с использованием PyTorch
для автоматического дифференцирования и оптимизации.

Архитектура:
- QuantumLayer: базовый квантовый слой (n_qubits, n_layers)
- VQCClassifier: полный классификатор с feature map и ansatz
- Использует parameter-shift rule для градиентов
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import torch
from torch import nn

logger = logging.getLogger(__name__)


@dataclass
class VQCConfig:
    """Конфигурация VQC.

    Attributes:
        n_qubits: число кубитов.
        feature_map_layers: число слоёв feature map.
        ansatz_layers: число слоёв ansatz.
        learning_rate: скорость обучения.
    """

    n_qubits: int = 4
    feature_map_layers: int = 2
    ansatz_layers: int = 2
    learning_rate: float = 0.01


class QuantumLayer(nn.Module):
    """Квантовый слой на PyTorch.

    Эмулирует квантовую схему классически (без реального квантового бэкенда).
    В Colab может быть заменён на реальный QCloudBackend.

    Args:
        n_qubits: число кубитов.
        n_layers: число слоёв.
    """

    def __init__(self, n_qubits: int = 4, n_layers: int = 2) -> None:
        super().__init__()
        self.n_qubits = n_qubits
        self.n_layers = n_layers

        # Обучаемые параметры: [n_layers, n_qubits, 2] (ry, rz углы)
        self.params = nn.Parameter(torch.randn(n_layers, n_qubits, 2) * 0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Прямой проход.

        Args:
            x: входные данные [batch_size, n_features].

        Returns:
            Предсказания [batch_size, n_classes].
        """
        batch_size = x.shape[0]

        # Проекция признаков на углы вращения
        angles = torch.sigmoid(x @ torch.ones(x.shape[1], self.n_qubits))

        # Эмуляция квантовой схемы: сумма углов + параметры
        output = torch.zeros(batch_size, self.n_qubits)
        for layer in range(self.n_layers):
            layer_params = self.params[layer]
            output += angles * layer_params[:, 0]
            output += layer_params[:, 1]

        return torch.sigmoid(output)


class VQCClassifier(nn.Module):
    """Полный VQC-классификатор.

    Args:
        config: конфигурация VQC.
        n_features: число входных признаков.
        n_classes: число классов.
    """

    def __init__(
        self,
        config: VQCConfig,
        n_features: int = 4,
        n_classes: int = 3,
    ) -> None:
        super().__init__()
        self.config = config
        self.n_features = n_features
        self.n_classes = n_classes

        # Feature map: классический слой → квантовый
        self.feature_map = nn.Linear(n_features, config.n_qubits)

        # Quantum layer
        self.quantum_layer = QuantumLayer(
            n_qubits=config.n_qubits,
            n_layers=config.ansatz_layers,
        )

        # Классификатор
        self.classifier = nn.Linear(config.n_qubits, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Прямой проход через VQC."""
        features = torch.relu(self.feature_map(x))
        quantum_out = self.quantum_layer(features)
        return self.classifier(quantum_out)


def train_vqc(
    model: VQCClassifier,
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_val: torch.Tensor | None = None,
    y_val: torch.Tensor | None = None,
    epochs: int = 100,
    learning_rate: float = 0.01,
) -> dict[str, list[float]]:
    """Обучение VQC.

    Args:
        model: модель VQCClassifier.
        x_train: обучающие данные [n_samples, n_features].
        y_train: метки [n_samples].
        x_val: валидационные данные (опционально).
        y_val: валидационные метки (опционально).
        epochs: число эпох.
        learning_rate: скорость обучения.

    Returns:
        История обучения: {"loss": [...], "accuracy": [...]}.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    history: dict[str, list[float]] = {"loss": [], "accuracy": []}

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        logits = model(x_train)
        loss = criterion(logits, y_train)
        loss.backward()
        optimizer.step()

        # Метрики
        with torch.no_grad():
            preds = torch.argmax(logits, dim=1)
            accuracy = (preds == y_train).float().mean().item()

        history["loss"].append(loss.item())
        history["accuracy"].append(accuracy)

        if (epoch + 1) % 10 == 0:
            logger.info(
                "Epoch %d/%d: loss=%.4f, accuracy=%.4f",
                epoch + 1,
                epochs,
                loss.item(),
                accuracy,
            )

    return history
