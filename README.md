# Quantum Workspace

Professional quantum computing environment for Google Colab.

## Structure
- configs/ — YAML configuration files
- src/core/ — Config loader, logger, exceptions, data models
- src/utils/ — Quantum circuits, backend factory, metrics, decorators
- src/pipelines/ — Bell test, teleportation, Deutsch-Jozsa
- notebooks/ — Entry point (00_environment_setup.ipynb)
- tests/ — Unit tests (6/6 passed)

## Quick Start
1. Open notebooks/00_environment_setup.ipynb
2. Run all cells
3. Add secrets in Colab: QCLOUD_API_KEY, OCTILLION_TOKEN

## Backends
- WK_C180 (180 qubits, superconducting)
- PQPUMESH8 (3 qubits, photonic)
- Snowdrop 8q ver2 (Octillion)
- CPUQVM (local simulator)
- CUDA-Q (NVIDIA GPU simulator)

## Usage
from pipelines.bell_test import BellTestPipeline
from core.config_loader import get_config

cfg = get_config()
result = BellTestPipeline(cfg).run()

## Testing
import pytest
pytest.main(['tests/', '-v'])
