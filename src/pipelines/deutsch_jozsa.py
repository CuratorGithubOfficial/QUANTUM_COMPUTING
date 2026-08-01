
"""Пайплайн алгоритма Дойча-Йожи."""
import logging
import time
from typing import Optional
from pyqpanda3.qcloud import QCloudOptions
from pyqpanda3.core import H, X, CNOT, QProg, measure
from core.config_loader import AppConfig
from core.models import DeutschJozsaResult
from utils.backend_factory import create_qcloud_backend
from utils.decorators import timer
from utils.metrics import print_results_table

logger = logging.getLogger(__name__)

class DeutschJozsaPipeline:
    """Пайплайн алгоритма Дойча-Йожи на реальном чипе."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.backend = None

    @timer
    def run(self, oracle_type: Optional[str] = None) -> DeutschJozsaResult:
        """
        Запускает алгоритм Дойча-Йожи.

        Args:
            oracle_type: Тип оракула ("balanced" или "constant").
                         Если None, берется из конфига.

        Returns:
            DeutschJozsaResult с результатом классификации.
        """
        if oracle_type is None:
            oracle_type = self.config.deutsch_jozsa.oracle_type

        logger.info("=" * 50)
        logger.info("DEUTSCH-JOZSA ALGORITHM")
        logger.info(f"Oracle type: {oracle_type}")
        logger.info("=" * 50)

        self.backend = create_qcloud_backend(chip=self.config.backends.qcloud.chip)

        # Строим схему
        prog = QProg()
        # Вспомогательный кубит в |−⟩
        prog << X(2) << H(2)
        # Суперпозиция входов
        prog << H(0) << H(1)

        # Оракул
        if oracle_type == "balanced":
            # f(x₀,x₁) = x₀ ⊕ x₁
            prog << CNOT(0, 2) << CNOT(1, 2)
        # constant: ничего не делаем (f(x)=0)

        # Финальный Адамар и измерение
        prog << H(0) << H(1)
        prog << measure([0, 1], [0, 1])

        # Запуск
        options = QCloudOptions()
        options.set_mapping(True)
        options.set_optimization(True)
        options.set_amend(True)

        shots = self.config.deutsch_jozsa.shots
        logger.info(f"Running with {shots} shots...")
        job = self.backend.run(prog, shots=shots, options=options)
        logger.info(f"Job ID: {job.job_id()}")

        while True:
            s = str(job.status())
            logger.info(f"  Status: {s}")
            if s in ("JobStatus.FINISHED", "FINISHED"):
                break
            time.sleep(1)

        result = job.result()
        probs = result.get_probs()
        counts = result.get_counts()

        # Анализ: если |00⟩ доминирует → константная, иначе → сбалансированная
        prob_00 = 0.0
        for k, v in (probs or {}).items():
            bits = format(int(k, 16), '02b') if k.startswith('0x') else k.zfill(2)
            if bits == '00':
                prob_00 = v

        is_constant = prob_00 > 0.5
        predicted_type = "constant" if is_constant else "balanced"
        correct = predicted_type == oracle_type

        metrics = {
            "Probability |00⟩": prob_00,
            "Predicted type": predicted_type,
            "Actual type": oracle_type,
            "Correct": correct,
        }
        if counts:
            metrics["Total counts"] = sum(counts.values())

        print_results_table("DEUTSCH-JOZSA RESULTS", metrics)

        if correct:
            logger.info(f"✓ Algorithm worked correctly! Function is {oracle_type}.")
        else:
            logger.info(f"✗ Classification failed. Predicted: {predicted_type}, actual: {oracle_type}")

        return DeutschJozsaResult(
            probability_00=prob_00,
            is_constant=is_constant,
            oracle_type=oracle_type,
            counts=counts or {}
        )
