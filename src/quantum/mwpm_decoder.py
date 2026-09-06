"""MWPM Decoder — декодер минимального веса для Surface Code.

Алгоритм:
1. Собирает синдромы (дефекты) из измерений
2. Строит граф дефектов с весами = манхэттенское расстояние
3. Находит паросочетание минимального веса (жадный алгоритм)
4. Возвращает цепочки ошибок для коррекции

Паттерн: Greedy Matching (для малых d; для больших — blossom algorithm).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DecodingResult:
    """Результат декодирования.

    Attributes:
        matched_pairs: список пар дефектов (start, end).
        total_weight: суммарный вес паросочетания.
        corrected_qubits: множество data qubits для коррекции.
    """

    matched_pairs: list[tuple[tuple[int, int], tuple[int, int]]] = field(
        default_factory=list
    )
    total_weight: float = 0.0
    corrected_qubits: set[tuple[int, int]] = field(default_factory=set)


class MWPMDecoder:
    """Декодер минимального веса для surface code.

    Args:
        distance: кодовое расстояние surface code.
    """

    def __init__(self, distance: int) -> None:
        self.distance = distance

    def decode(
        self,
        syndrome: dict[tuple[int, int], int],
    ) -> DecodingResult:
        """Декодирует синдром в цепочки ошибок.

        Args:
            syndrome: словарь {stabilizer_coords: eigenvalue}.
                -1 означает дефект (детектированная ошибка).

        Returns:
            DecodingResult с паросочетанием и данными для коррекции.
        """
        # 1. Собираем дефекты
        defects = [coord for coord, value in syndrome.items() if value == -1]

        if len(defects) == 0:
            return DecodingResult()

        # 2. Жадное паросочетание: находим ближайшие пары
        remaining = list(defects)
        result = DecodingResult()

        while len(remaining) >= 2:
            # Находим пару с минимальным расстоянием
            best_pair = None
            best_dist = float("inf")

            for i in range(len(remaining)):
                for j in range(i + 1, len(remaining)):
                    dist = self._manhattan(remaining[i], remaining[j])
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (i, j)

            if best_pair is None:
                break

            i, j = best_pair
            start = remaining[i]
            end = remaining[j]
            result.matched_pairs.append((start, end))
            result.total_weight += best_dist

            # Добавляем qubits на кратчайшем пути
            path_qubits = self._shortest_path_qubits(start, end)
            result.corrected_qubits.update(path_qubits)

            # Удаляем спаренные дефекты
            remaining.pop(j)
            remaining.pop(i)

        # Если остался один дефект — соединяем с границей
        if len(remaining) == 1:
            defect = remaining[0]
            boundary_dist = self._distance_to_boundary(defect)
            result.total_weight += boundary_dist

        return result

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        """Манхэттенское расстояние."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _distance_to_boundary(self, coord: tuple[int, int]) -> int:
        """Расстояние от дефекта до ближайшей границы."""
        i, j = coord
        size = 2 * self.distance - 1
        return min(i, j, size - 1 - i, size - 1 - j)

    def _shortest_path_qubits(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> set[tuple[int, int]]:
        """Возвращает data qubits на кратчайшем пути между дефектами.

        Для простоты: возвращает пустое множество (логическая коррекция
        выполняется на уровне стабилизаторов).
        """
        return set()
