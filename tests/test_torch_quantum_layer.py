"""Тесты для Torch Quantum Layer — 5 тестов."""

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.torch_quantum_layer import (
    QuantumLayer,
    VQCClassifier,
    VQCConfig,
    train_vqc,
)


class TestVQCConfig:
    """Тесты конфигурации."""

    def test_default_config(self):
        config = VQCConfig()
        assert config.n_qubits == 4
        assert config.feature_map_layers == 2
        assert config.ansatz_layers == 2
        assert config.learning_rate == 0.01

    def test_custom_config(self):
        config = VQCConfig(n_qubits=8, ansatz_layers=4)
        assert config.n_qubits == 8
        assert config.ansatz_layers == 4


class TestQuantumLayer:
    """Тесты квантового слоя."""

    def test_forward_shape(self):
        layer = QuantumLayer(n_qubits=4, n_layers=2)
        x = torch.randn(10, 3)
        output = layer(x)
        assert output.shape == (10, 4)

    def test_params_shape(self):
        layer = QuantumLayer(n_qubits=4, n_layers=2)
        assert layer.params.shape == (2, 4, 2)


class TestVQCClassifier:
    """Тесты классификатора."""

    def test_forward_shape(self):
        config = VQCConfig(n_qubits=4)
        model = VQCClassifier(config, n_features=4, n_classes=3)
        x = torch.randn(8, 4)
        output = model(x)
        assert output.shape == (8, 3)

    def test_train_vqc(self):
        config = VQCConfig(n_qubits=4, ansatz_layers=1)
        model = VQCClassifier(config, n_features=2, n_classes=2)

        # Простые данные
        x_train = torch.randn(20, 2)
        y_train = torch.randint(0, 2, (20,))

        history = train_vqc(model, x_train, y_train, epochs=5)

        assert "loss" in history
        assert "accuracy" in history
        assert len(history["loss"]) == 5
        assert len(history["accuracy"]) == 5
