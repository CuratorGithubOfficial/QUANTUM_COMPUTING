"""Тесты для Environment — 5 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.environment import Environment, get_environment, init_environment


class TestEnvironmentInit:
    """Тесты инициализации."""

    def test_detect_project_root(self):
        """Тест: автоопределение корня проекта."""
        env = Environment()
        assert env.project_root == ROOT
        assert env.src_path == ROOT / "src"
        assert env.config_path == ROOT / "configs"

    def test_explicit_root(self, tmp_path):
        """Тест: явное указание корня."""
        env = Environment(project_root=tmp_path)
        assert env.project_root == tmp_path
        assert env.src_path == tmp_path / "src"

    def test_is_colab_false(self):
        """Тест: локально не Colab."""
        env = Environment()
        assert env.is_colab is False


class TestEnvironmentDirectories:
    """Тесты директорий."""

    def test_outputs_created(self):
        """Тест: директории outputs создаются."""
        env = Environment()
        assert env.outputs_path.exists()
        assert (env.outputs_path / "models").exists()
        assert (env.outputs_path / "logs").exists()
        assert (env.outputs_path / "artifacts").exists()


class TestEnvironmentSingleton:
    """Тесты глобального инстанса."""

    def test_get_environment_returns_singleton(self):
        """Тест: get_environment возвращает один инстанс."""
        env1 = get_environment()
        env2 = get_environment()
        assert env1 is env2

    def test_init_environment(self):
        """Тест: init_environment пересоздаёт инстанс."""
        env1 = init_environment()
        env2 = init_environment()
        assert env1 is not env2  # каждый вызов создаёт новый
