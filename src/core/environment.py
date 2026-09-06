"""Environment — управление окружением и путями проекта.

Обеспечивает:
- Определение корня проекта (работает и в Colab, и локально)
- Управление PYTHONPATH
- Создание необходимых директорий
- Доступ к секретам (colab.userdata или переменные окружения)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class Environment:
    """Управление окружением проекта.

    Определяет корень проекта, настраивает пути и секреты.
    Работает в двух режимах:
    - Colab: /content/drive/MyDrive/Colab_Projects/quantum_workspace
    - Локально: корень git-репозитория

    Attributes:
        project_root: путь к корню проекта.
        src_path: путь к src/.
        config_path: путь к configs/.
        outputs_path: путь к outputs/.
        is_colab: True, если запущено в Google Colab.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = self._detect_project_root(project_root)
        self._src_path = self._project_root / "src"
        self._config_path = self._project_root / "configs"
        self._outputs_path = self._project_root / "outputs"
        self._is_colab = self._detect_colab()

        self._setup_paths()
        self._create_directories()

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def src_path(self) -> Path:
        return self._src_path

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def outputs_path(self) -> Path:
        return self._outputs_path

    @property
    def is_colab(self) -> bool:
        return self._is_colab

    @staticmethod
    def _detect_colab() -> bool:
        """Определяет, запущено ли в Google Colab."""
        try:
            import importlib.util

            return importlib.util.find_spec("google.colab") is not None
        except ImportError:
            return False

    @staticmethod
    def _detect_project_root(explicit_root: Path | None) -> Path:
        """Определяет корень проекта.

        Приоритет:
        1. Явно переданный путь
        2. Переменная окружения QUANTUM_WORKSPACE_ROOT
        3. Поиск от текущей директории вверх по дереву
        4. Colab-путь по умолчанию
        """
        if explicit_root is not None:
            return explicit_root

        env_root = os.environ.get("QUANTUM_WORKSPACE_ROOT")
        if env_root:
            return Path(env_root)

        # Поиск вверх по дереву: ищем директорию с src/ и configs/
        current = Path.cwd()
        for parent in [current, *current.parents]:
            if (parent / "src").exists() and (parent / "configs").exists():
                return parent

        # Colab fallback
        colab_root = Path("/content/drive/MyDrive/Colab_Projects/quantum_workspace")
        if colab_root.exists():
            return colab_root

        # Последний fallback — текущая директория
        return current

    def _setup_paths(self) -> None:
        """Добавляет src/ в sys.path."""
        if str(self._src_path) not in sys.path:
            sys.path.insert(0, str(self._src_path))
            logger.debug("Added to sys.path: %s", self._src_path)

    def _create_directories(self) -> None:
        """Создаёт необходимые директории."""
        for path in [
            self._outputs_path,
            self._outputs_path / "models",
            self._outputs_path / "logs",
            self._outputs_path / "artifacts",
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def get_secret(self, key_name: str) -> str:
        """Получает секрет из colab.userdata или переменных окружения.

        Args:
            key_name: имя секрета (например, "QCLOUD_API_KEY").

        Returns:
            Значение секрета.

        Raises:
            ValueError: если секрет не найден.
        """
        # Пробуем colab.userdata
        if self._is_colab:
            try:
                from google.colab import userdata  # type: ignore

                value = userdata.get(key_name)
                if value:
                    return value
            except ImportError:
                pass

        # Пробуем переменные окружения
        value = os.environ.get(key_name)
        if value:
            return value

        raise ValueError(
            f"Secret '{key_name}' not found. "
            f"Set it in colab.userdata or environment variables."
        )


# Глобальный инстанс
_environment: Environment | None = None


def get_environment() -> Environment:
    """Возвращает глобальный инстанс Environment."""
    global _environment
    if _environment is None:
        _environment = Environment()
    return _environment


def init_environment(project_root: Path | None = None) -> Environment:
    """Инициализирует глобальный инстанс Environment."""
    global _environment
    _environment = Environment(project_root)
    return _environment
