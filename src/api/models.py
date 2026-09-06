"""Pydantic-модели для API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BellTestRequest(BaseModel):
    """Запрос на запуск теста Белла."""

    shots_per_correlator: int = Field(default=2000, ge=100, le=10000)
    backend_name: str = Field(default="mock")
    angles_a: list[float] = Field(default=[0.0, 1.5708])
    angles_b: list[float] = Field(default=[0.7854, 2.3562])


class BellTestResponse(BaseModel):
    """Ответ с результатами теста Белла."""

    job_id: str
    status: str
    s_value: float | None = None
    inequality_violated: bool | None = None
    correlators: list[float] | None = None
    error: str | None = None


class TeleportationRequest(BaseModel):
    """Запрос на запуск телепортации."""

    state_to_teleport: str = Field(default="|1>")
    shots: int = Field(default=3000, ge=100, le=10000)
    backend_name: str = Field(default="mock")
    physical_qubits: list[int] = Field(default=[0, 1, 2])


class TeleportationResponse(BaseModel):
    """Ответ с результатами телепортации."""

    job_id: str
    status: str
    fidelity: float | None = None
    post_selection_rate: float | None = None
    error: str | None = None


class JobStatusResponse(BaseModel):
    """Статус задания."""

    job_id: str
    status: str
    result: dict | None = None
    error: str | None = None
