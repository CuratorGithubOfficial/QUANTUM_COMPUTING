
"""Пайплайн квантовой телепортации."""
import logging
import time
from typing import Optional
from pyqpanda3.qcloud import QCloudOptions
from core.config_loader import AppConfig
from core.models import TeleportationResult
from utils.quantum_helpers import build_teleportation_circuit
from utils.backend_factory import create_qcloud_backend
from utils.decorators import timer
from utils.metrics import compute_fidelity_from_probs, compute_post_selected_fidelity, print_results_table

logger = logging.getLogger(__name__)

class TeleportationPipeline:
    """Пайплайн квантовой телепортации на реальном чипе."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.backend = None

    @timer
    def run(self) -> TeleportationResult:
        """
        Запускает телепортацию состояния.

        Returns:
            TeleportationResult с fidelity.
        """
        logger.info("=" * 50)
        logger.info("QUANTUM TELEPORTATION")
        logger.info("=" * 50)

        cfg = self.config.teleportation
        self.backend = create_qcloud_backend(chip=self.config.backends.qcloud.chip)

        # Строим схему
        logger.info(f"Building circuit for state: {cfg.state_to_teleport}")
        state_gate = "X" if cfg.state_to_teleport == "|1⟩" else "H"
        prog = build_teleportation_circuit(state_gate)

        # Настройка опций с физическими кубитами
        options = QCloudOptions()
        options.set_mapping(False)
        options.set_optimization(True)
        options.set_amend(True)
        options.set_specified_block(cfg.physical_qubits)

        logger.info(f"Physical qubits: {cfg.physical_qubits}")
        logger.info(f"Shots: {cfg.shots}, Post-select: {cfg.post_select}")

        # Запуск
        logger.info("Submitting job...")
        job = self.backend.run(prog, shots=cfg.shots, options=options)
        logger.info(f"Job ID: {job.job_id()}")

        # Ожидание
        while True:
            s = str(job.status())
            logger.info(f"  Status: {s}")
            if s in ("JobStatus.FINISHED", "FINISHED"):
                break
            time.sleep(1)

        result = job.result()
        probs = result.get_probs()
        counts = result.get_counts()

        if not probs:
            raise RuntimeError("No probabilities returned from backend")

        # Анализ
        if cfg.post_select:
            fidelity = compute_post_selected_fidelity(probs, target_state="1")
            post_select_rate = sum(
                prob for bs, prob in probs.items()
                if (format(int(bs, 16), '03b') if bs.startswith('0x') else bs.zfill(3))[1:3] == "00"
            )
        else:
            fidelity = compute_fidelity_from_probs(probs, target_state="1")
            post_select_rate = None

        metrics = {
            "Fidelity": fidelity or 0.0,
            "Post-selection rate": post_select_rate or 0.0,
        }
        if counts:
            total = sum(counts.values())
            bob_1 = sum(v for k, v in counts.items() if k[0] == '1')
            metrics["Bob in |1⟩"] = bob_1 / total

        print_results_table("TELEPORTATION RESULTS", metrics)
        return TeleportationResult(
            fidelity=fidelity or 0.0,
            bob_in_target_state=metrics.get("Bob in |1⟩", 0.0),
            post_selection_rate=post_select_rate,
            counts=counts,
            physical_qubits=cfg.physical_qubits
        )
