
"""Фабрика для создания квантовых бэкендов."""
import os
import logging
from typing import Any
from pyqpanda3.qcloud import QCloudService
from core.exceptions import APIKeyNotFoundError, BackendConnectionError

logger = logging.getLogger(__name__)

def create_qcloud_backend(api_key: str = None, chip: str = "WK_C180") -> Any:
    """
    Создает и возвращает QCloud-бэкенд.

    Args:
        api_key: API-ключ. Если None, берется из QPANDA_QCLOUD_API_KEY.
        chip: Название чипа.

    Returns:
        QCloud-бэкенд.

    Raises:
        APIKeyNotFoundError: Если ключ не найден.
        BackendConnectionError: Если не удалось подключиться.
    """
    if api_key is None:
        api_key = os.environ.get("QPANDA_QCLOUD_API_KEY")
        if not api_key:
            raise APIKeyNotFoundError("QPANDA_QCLOUD_API_KEY")

    try:
        service = QCloudService(api_key)
        backend = service.backend(chip)
        logger.info(f"QCloud backend '{chip}' created successfully")
        return backend
    except Exception as e:
        raise BackendConnectionError(f"QCloud/{chip}", str(e))


def create_octillion_backend(token: str = None, chip: str = "Snowdrop 8q ver2") -> Any:
    """
    Создает и возвращает Octillion-бэкенд.

    Args:
        token: Токен доступа. Если None, берется из OCTILLION_TOKEN.
        chip: Название чипа.

    Returns:
        Octillion-бэкенд.
    """
    from octillion.client import Client

    if token is None:
        token = os.environ.get("OCTILLION_TOKEN")
        if not token:
            raise APIKeyNotFoundError("OCTILLION_TOKEN")

    try:
        client = Client(token)
        backend = client.remote(chip)
        logger.info(f"Octillion backend '{chip}' created successfully")
        return backend
    except Exception as e:
        raise BackendConnectionError(f"Octillion/{chip}", str(e))
