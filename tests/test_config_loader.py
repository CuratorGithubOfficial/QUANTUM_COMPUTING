"""Тесты для загрузчика конфига.

Исправление: удалены жёсткие пути Colab, добавлено автоопределение
корня проекта через Path(__file__).parent.parent.
"""

import sys
from pathlib import Path

import pytest

# Автоопределение корня проекта (работает и на Windows, и на Linux)
ROOT = Path(__file__).parent.parent
SRC_PATH = ROOT / "src"
CONFIG_PATH = ROOT / "configs" / "config.yaml"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from core.config_loader import AppConfig


def test_load_config_success():
    """Тест: успешная загрузка конфига."""
    config = AppConfig.from_yaml(CONFIG_PATH)

    assert config.environment == "colab"
    assert config.backends.qcloud.chip == "WK_C180"
    assert config.bell_test.classical_bound == 2.0
    assert len(config.bell_test.angles["a"]) == 2
    assert config.vqc.iris.random_state == 42


def test_load_config_file_not_found():
    """Тест: ошибка при отсутствии файла."""
    with pytest.raises(FileNotFoundError):
        AppConfig.from_yaml(Path("/nonexistent/config.yaml"))


def test_config_paths_exist():
    """Тест: проверка структуры конфига."""
    config = AppConfig.from_yaml(CONFIG_PATH)

    assert config.paths is not None
    assert config.logging is not None
    assert config.logging.level in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_backends_config_structure():
    """Тест: структура бэкендов."""
    config = AppConfig.from_yaml(CONFIG_PATH)

    assert config.backends.qcloud.default_shots > 0
    assert config.backends.octillion.default_shots > 0
    assert config.backends.cudaq.default_shots > 0
    assert isinstance(config.backends.local_simulator, str)


def test_vqc_config_values():
    """Тест: параметры VQC в допустимых диапазонах."""
    config = AppConfig.from_yaml(CONFIG_PATH)

    assert 0.0 < config.vqc.iris.test_size < 1.0
    assert config.vqc.iris.max_iterations > 0
    assert config.vqc.iris.restarts > 0
    assert config.vqc.multiclass.n_qubits > 0
