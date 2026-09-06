"""Тесты для FastAPI приложения."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from api.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealth:
    """Тесты health-check."""

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestBellTest:
    """Тесты Bell test endpoint."""

    def test_bell_test_success(self, client):
        from adapters.mock_adapter import MockBackend  # noqa: F401

        response = client.post(
            "/experiments/bell",
            json={
                "shots_per_correlator": 100,
                "backend_name": "mock",
                "angles_a": [0.0, 1.5708],
                "angles_b": [0.7854, 2.3562],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "finished"
        assert data["s_value"] is not None


class TestTeleportation:
    """Тесты teleportation endpoint."""

    def test_teleportation_success(self, client):
        from adapters.mock_adapter import MockBackend  # noqa: F401

        response = client.post(
            "/experiments/teleportation",
            json={
                "state_to_teleport": "|1>",
                "shots": 100,
                "backend_name": "mock",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "finished"
        assert data["fidelity"] is not None
