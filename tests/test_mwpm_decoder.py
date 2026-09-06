"""Тесты для MWPM Decoder — 5 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from quantum.mwpm_decoder import MWPMDecoder


class TestMWPMDecoderInit:
    """Тесты инициализации."""

    def test_init(self):
        decoder = MWPMDecoder(distance=3)
        assert decoder.distance == 3


class TestMWPMDecode:
    """Тесты декодирования."""

    def test_no_defects(self):
        decoder = MWPMDecoder(distance=3)
        syndrome = {(0, 1): +1, (2, 1): +1}
        result = decoder.decode(syndrome)
        assert len(result.matched_pairs) == 0
        assert result.total_weight == 0.0

    def test_single_defect(self):
        decoder = MWPMDecoder(distance=3)
        syndrome = {(2, 2): -1}  # один дефект (внутренний)
        result = decoder.decode(syndrome)
        assert result.total_weight > 0

    def test_two_defects(self):
        decoder = MWPMDecoder(distance=3)
        syndrome = {(0, 1): -1, (0, 3): -1}  # два дефекта
        result = decoder.decode(syndrome)
        assert len(result.matched_pairs) == 1
        assert result.total_weight == 2  # расстояние 2

    def test_four_defects(self):
        decoder = MWPMDecoder(distance=3)
        syndrome = {
            (0, 1): -1,
            (0, 3): -1,
            (2, 1): -1,
            (2, 3): -1,
        }
        result = decoder.decode(syndrome)
        assert len(result.matched_pairs) == 2


class TestManhattan:
    """Тесты расстояния."""

    def test_manhattan(self):
        assert MWPMDecoder._manhattan((0, 0), (2, 2)) == 4
        assert MWPMDecoder._manhattan((0, 0), (0, 5)) == 5
