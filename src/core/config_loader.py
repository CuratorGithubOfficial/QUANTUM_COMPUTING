import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PathsConfig:
    raw_data: str
    processed_data: str
    model_weights: str
    logs: str


@dataclass
class QCloudBackend:
    chip: str
    default_shots: int


@dataclass
class OctillionBackend:
    chip: str
    default_shots: int


@dataclass
class CudaqBackend:
    default_shots: int


@dataclass
class BackendsConfig:
    qcloud: QCloudBackend
    octillion: OctillionBackend
    cudaq: CudaqBackend
    local_simulator: str


@dataclass
class BellTestConfig:
    angles: dict[str, list[float]]
    classical_bound: float
    quantum_bound: float
    shots_per_correlator: int


@dataclass
class SuperdenseCodingConfig:
    messages: dict[str, str]
    shots_per_message: int


@dataclass
class TeleportationConfig:
    state_to_teleport: str
    physical_qubits: list[int]
    shots: int
    use_qif: bool
    post_select: bool


@dataclass
class DeutschJozsaConfig:
    n_qubits: int
    oracle_type: str
    shots: int


@dataclass
class IrisVQCConfig:
    test_size: float
    random_state: int
    feature_range: list[float]
    feature_map_layers: int
    ansatz_layers: int
    optimizer: str
    max_iterations: int
    restarts: int


@dataclass
class MulticlassVQCConfig:
    n_qubits: int
    test_size: float
    random_state: int
    feature_map_layers: int
    ansatz_layers: int
    optimizer: str
    max_iterations: int
    n_params: int


@dataclass
class VQCConfig:
    iris: IrisVQCConfig
    multiclass: MulticlassVQCConfig


@dataclass
class LoggingConfig:
    level: str
    format: str
    file: str


@dataclass
class AppConfig:
    environment: str
    paths: PathsConfig
    backends: BackendsConfig
    bell_test: BellTestConfig
    superdense_coding: SuperdenseCodingConfig
    teleportation: TeleportationConfig
    deutsch_jozsa: DeutschJozsaConfig
    vqc: VQCConfig
    logging: LoggingConfig

    @classmethod
    def from_yaml(cls, config_path: Path) -> "AppConfig":
        """Загружает и валидирует конфиг из YAML файла."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        try:
            config = cls(
                environment=raw["environment"],
                paths=PathsConfig(**raw["paths"]),
                backends=BackendsConfig(
                    qcloud=QCloudBackend(**raw["backends"]["qcloud"]),
                    octillion=OctillionBackend(**raw["backends"]["octillion"]),
                    cudaq=CudaqBackend(**raw["backends"]["cudaq"]),
                    local_simulator=raw["backends"]["local_simulator"],
                ),
                bell_test=BellTestConfig(**raw["bell_test"]),
                superdense_coding=SuperdenseCodingConfig(**raw["superdense_coding"]),
                teleportation=TeleportationConfig(**raw["teleportation"]),
                deutsch_jozsa=DeutschJozsaConfig(**raw["deutsch_jozsa"]),
                vqc=VQCConfig(
                    iris=IrisVQCConfig(**raw["vqc"]["iris"]),
                    multiclass=MulticlassVQCConfig(**raw["vqc"]["multiclass"]),
                ),
                logging=LoggingConfig(**raw["logging"]),
            )
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except KeyError as e:
            logger.error(f"Missing required config section: {e}")
            raise


# Глобальный объект конфига
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Возвращает текущий объект конфигурации."""
    if _config is None:
        raise RuntimeError("Config not initialized. Call init_config() first.")
    return _config


def init_config(config_path: Path):
    """Инициализирует глобальный конфиг."""
    global _config
    _config = AppConfig.from_yaml(config_path)
