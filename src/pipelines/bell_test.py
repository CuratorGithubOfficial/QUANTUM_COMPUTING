
"""Пайплайн теста Белла (нарушение неравенств)."""
import logging
import numpy as np
from typing import Optional
from core.config_loader import AppConfig
from core.models import BellTestResult, BellCorrelator
from utils.quantum_helpers import measure_correlation
from utils.backend_factory import create_qcloud_backend
from utils.decorators import timer
from utils.metrics import print_results_table

logger = logging.getLogger(__name__)

class BellTestPipeline:
    """Пайплайн проверки нарушения неравенства Белла на реальном чипе."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.backend = None

    @timer
    def run(self) -> BellTestResult:
        """
        Запускает полный тест Белла.

        Returns:
            BellTestResult с корреляторами и S-значением.
        """
        logger.info("=" * 50)
        logger.info("BELL INEQUALITY TEST")
        logger.info("=" * 50)

        # Подключение к бэкенду
        logger.info(f"Connecting to QCloud backend: {self.config.backends.qcloud.chip}")
        self.backend = create_qcloud_backend(chip=self.config.backends.qcloud.chip)

        # Углы из конфига
        a1, a2 = self.config.bell_test.angles['a']
        b1, b2 = self.config.bell_test.angles['b']
        shots = self.config.bell_test.shots_per_correlator

        # Измеряем 4 коррелятора
        logger.info("Measuring correlators...")
        correlators = []
        for theta_a, theta_b, label in [
            (a1, b1, "E(a₁,b₁)"),
            (a1, b2, "E(a₁,b₂)"),
            (a2, b1, "E(a₂,b₁)"),
            (a2, b2, "E(a₂,b₂)"),
        ]:
            logger.info(f"  Measuring {label}...")
            expectation = measure_correlation(self.backend, theta_a, theta_b, shots)
            correlators.append(BellCorrelator(
                angle_a=theta_a,
                angle_b=theta_b,
                expectation=expectation,
                shots=shots
            ))
            logger.info(f"  {label} = {expectation:+.4f}")

        # Считаем S
        result = BellTestResult(
            correlators=correlators,
            classical_bound=self.config.bell_test.classical_bound,
            quantum_bound=self.config.bell_test.quantum_bound
        )

        # Вывод результатов
        metrics = {
            "E(a₁,b₁)": correlators[0].expectation,
            "E(a₁,b₂)": correlators[1].expectation,
            "E(a₂,b₁)": correlators[2].expectation,
            "E(a₂,b₂)": correlators[3].expectation,
            "S": result.S_value,
            "Classical bound": result.classical_bound,
            "Quantum bound": result.quantum_bound,
        }
        print_results_table("BELL TEST RESULTS", metrics)

        if result.inequality_violated:
            logger.info(f"✓ BELL INEQUALITY VIOLATED! S = {result.S_value:.4f} > 2")
        else:
            logger.info(f"  Inequality not violated. S = {result.S_value:.4f} ≤ 2")

        return result
