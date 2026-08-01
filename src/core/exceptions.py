
"""Кастомные исключения для квантового проекта."""

class QuantumProjectError(Exception):
    """Базовое исключение проекта."""
    pass

class BackendConnectionError(QuantumProjectError):
    """Ошибка подключения к квантовому бэкенду."""
    def __init__(self, backend_name: str, message: str = ""):
        self.backend_name = backend_name
        super().__init__(f"Backend '{backend_name}' connection failed. {message}")

class JobExecutionError(QuantumProjectError):
    """Ошибка выполнения квантового задания."""
    def __init__(self, job_id: str, status: str, message: str = ""):
        self.job_id = job_id
        self.status = status
        super().__init__(f"Job '{job_id}' failed with status '{status}'. {message}")

class ConfigValidationError(QuantumProjectError):
    """Ошибка валидации конфигурации."""
    pass

class APIKeyNotFoundError(QuantumProjectError):
    """API-ключ не найден в переменных окружения."""
    def __init__(self, key_name: str):
        super().__init__(f"API key '{key_name}' not found. Set it in colab.userdata or environment variables.")
