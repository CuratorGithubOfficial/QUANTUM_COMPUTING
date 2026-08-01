
"""Метрики и визуализация для квантовых экспериментов."""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def compute_fidelity_from_probs(
    probs: Dict[str, float],
    target_state: str = "1",
    bob_index: int = 0
) -> float:
    """
    Вычисляет fidelity Боба из словаря вероятностей.

    Args:
        probs: Словарь {bitstring: probability}.
        target_state: Ожидаемое состояние Боба ('0' или '1').
        bob_index: Индекс бита Боба (0 — старший бит).

    Returns:
        Fidelity (доля измерений с Бобом в target_state).
    """
    fidelity = 0.0
    for bs, prob in probs.items():
        bits = format(int(bs, 16), '03b') if bs.startswith('0x') else bs.zfill(3)
        if bits[bob_index] == target_state:
            fidelity += prob
    return fidelity


def compute_post_selected_fidelity(
    probs: Dict[str, float],
    target_state: str = "1",
    post_select_bits: str = "00",
    bob_index: int = 0
) -> Optional[float]:
    """
    Вычисляет fidelity с пост-селекцией по измерениям Алисы.

    Args:
        probs: Словарь вероятностей.
        target_state: Ожидаемое состояние Боба.
        post_select_bits: Биты Алисы для отбора (например, "00").
        bob_index: Индекс бита Боба.

    Returns:
        Fidelity среди отобранных исходов, или None если таких нет.
    """
    bob_correct = 0.0
    total_selected = 0.0
    for bs, prob in probs.items():
        bits = format(int(bs, 16), '03b') if bs.startswith('0x') else bs.zfill(3)
        alice_bits = bits[1] + bits[2]  # c1, c2 — измерения Алисы
        bob_bit = bits[bob_index]
        if alice_bits == post_select_bits:
            total_selected += prob
            if bob_bit == target_state:
                bob_correct += prob

    if total_selected == 0:
        return None
    return bob_correct / total_selected


def print_results_table(title: str, metrics: Dict[str, float], precision: int = 4):
    """Выводит таблицу результатов в консоль."""
    logger.info("=" * 50)
    logger.info(title)
    logger.info("=" * 50)
    for key, value in metrics.items():
        logger.info(f"  {key}: {value:.{precision}f}")
    logger.info("=" * 50)
