"""API-роуты для квантовых экспериментов."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from api.models import (
    BellTestRequest,
    BellTestResponse,
    JobStatusResponse,
    TeleportationRequest,
    TeleportationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/bell", response_model=BellTestResponse)
async def run_bell_test(request: BellTestRequest) -> BellTestResponse:
    """Запускает тест Белла."""
    try:
        from core.interfaces import get_backend
        from utils.quantum_helpers import measure_correlation

        backend = get_backend(request.backend_name)

        correlators = []
        for theta_a in request.angles_a:
            for theta_b in request.angles_b:
                expectation = measure_correlation(
                    backend,
                    theta_a,
                    theta_b,
                    shots=request.shots_per_correlator,
                )
                correlators.append(expectation)

        s_value = sum(correlators[:3]) - correlators[3]
        violated = s_value > 2.0

        return BellTestResponse(
            job_id="bell_test_0001",
            status="finished",
            s_value=s_value,
            inequality_violated=violated,
            correlators=correlators,
        )
    except (ValueError, RuntimeError, KeyError) as exc:
        logger.error("Bell test failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/teleportation", response_model=TeleportationResponse)
async def run_teleportation(request: TeleportationRequest) -> TeleportationResponse:
    """Запускает квантовую телепортацию."""
    try:
        from core.interfaces import get_backend
        from utils.quantum_helpers import build_teleportation_circuit

        backend = get_backend(request.backend_name)
        circuit = build_teleportation_circuit(
            state_prep_gate="X" if request.state_to_teleport == "|1>" else "H"
        )
        result = backend.run(circuit, shots=request.shots)

        fidelity = 0.0
        if result.probabilities:
            for bitstring, prob in result.probabilities.items():
                bits = (
                    bitstring.zfill(3)
                    if not bitstring.startswith("0x")
                    else format(int(bitstring, 16), "03b")
                )
                if bits[0] == "1":
                    fidelity += prob

        return TeleportationResponse(
            job_id=result.job_id or "teleportation_0001",
            status="finished",
            fidelity=fidelity,
        )
    except (ValueError, RuntimeError, KeyError) as exc:
        logger.error("Teleportation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Возвращает статус задания."""
    return JobStatusResponse(job_id=job_id, status="finished")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> dict[str, str]:
    """Отменяет задание."""
    return {"job_id": job_id, "status": "cancelled"}
