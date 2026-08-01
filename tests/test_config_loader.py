
"""Тесты для загрузчика конфига."""
import pytest
import sys
from pathlib import Path

# Добавляем src в путь для импорта
SRC_PATH = Path("/content/drive/MyDrive/Colab_Projects/quantum_workspace/src")
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from core.config_loader import AppConfig

def test_load_config_success():
    """Тест: успешная загрузка конфига."""
    config_path = Path("/content/drive/MyDrive/Colab_Projects/quantum_workspace/configs/config.yaml")
    config = AppConfig.from_yaml(config_path)
    
    assert config.environment == "colab"
    assert config.backends.qcloud.chip == "WK_C180"
    assert config.bell_test.classical_bound == 2.0
    assert len(config.bell_test.angles['a']) == 2
    assert config.vqc.iris.random_state == 42

def test_load_config_file_not_found():
    """Тест: ошибка при отсутствии файла."""
    with pytest.raises(FileNotFoundError):
        AppConfig.from_yaml(Path("/nonexistent/config.yaml"))

def test_config_paths_exist():
    """Тест: проверка структуры конфига."""
    config_path = Path("/content/drive/MyDrive/Colab_Projects/quantum_workspace/configs/config.yaml")
    config = AppConfig.from_yaml(config_path)
    
    assert config.paths is not None
    assert config.logging is not None
    assert config.logging.level in ["DEBUG", "INFO", "WARNING", "ERROR"]
