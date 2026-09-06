"""Тесты для Quantum Chaos Monkey — 5 тестов."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.chaos_monkey import ChaosConfig, QuantumChaosMonkey


class TestChaosConfig:
    """Тесты конфигурации."""

    def test_default_config(self):
        config = ChaosConfig()
        assert config.failure_rate == 0.1
        assert config.delay_rate == 0.1
        assert config.max_delay == 1.0

    def test_custom_config(self):
        config = ChaosConfig(failure_rate=0.5, seed=42)
        assert config.failure_rate == 0.5
        assert config.seed == 42


class TestChaosMonkey:
    """Тесты внедрения хаоса."""

    def test_no_chaos_when_rates_zero(self):
        config = ChaosConfig(failure_rate=0.0, delay_rate=0.0)
        monkey = QuantumChaosMonkey(config)
        result = monkey.apply_chaos(lambda: "success")
        assert result.chaos_applied is False
        assert result.chaos_type == "none"
        assert result.chaos_result == "success"

    def test_always_fail(self):
        config = ChaosConfig(failure_rate=1.0, delay_rate=0.0)
        monkey = QuantumChaosMonkey(config)
        result = monkey.apply_chaos(lambda: "success")
        assert result.chaos_applied is True
        assert result.chaos_type == "failure"
        assert result.chaos_result is None

    def test_run_chaos_test(self):
        config = ChaosConfig(failure_rate=0.0, delay_rate=0.0)
        monkey = QuantumChaosMonkey(config)
        stats = monkey.run_chaos_test(lambda: "ok", n_iterations=5)
        assert stats["total"] == 5
        assert stats["failures"] == 0
        assert stats["successes"] == 5
