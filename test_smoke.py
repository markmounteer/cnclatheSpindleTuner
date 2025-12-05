"""
Smoke tests for CI - verifies basic imports work correctly.

These are pytest-style unit tests that verify the application code
can be imported without errors. The tests/ directory contains
application-specific spindle tuner test classes (not pytest tests).
"""

class TestImports:
    """Verify core modules can be imported."""

    def test_import_config(self):
        """Config module should import without error."""
        import config
        assert hasattr(config, 'MONITOR_PINS')
        assert hasattr(config, 'BASELINE_PARAMS')

    def test_import_tests_base(self):
        """Tests base module should import without error."""
        from tests.base import BaseTest, TestDescription, TARGETS
        assert BaseTest is not None
        assert TestDescription is not None
        assert TARGETS is not None

    def test_import_test_classes(self):
        """All spindle test classes should be importable."""
        from tests.base import BaseTest
        from tests.test_signal_chain import SignalChainTest
        from tests.test_preflight import PreflightTest
        from tests.test_encoder import EncoderTest
        from tests.test_open_loop import OpenLoopTest
        from tests.test_forward import ForwardTest
        from tests.test_reverse import ReverseTest
        from tests.test_rate_limit import RateLimitTest
        from tests.test_step import StepTest
        from tests.test_load import LoadTest
        from tests.test_steadystate import SteadyStateTest
        from tests.test_decel import DecelTest
        from tests.test_ramp import RampTest
        from tests.test_full_suite import FullSuiteTest
        from tests.test_watchdog import WatchdogTest

        # Verify they have required methods
        test_classes = [
            SignalChainTest,
            PreflightTest,
            EncoderTest,
            OpenLoopTest,
            ForwardTest,
            ReverseTest,
            RateLimitTest,
            StepTest,
            LoadTest,
            SteadyStateTest,
            DecelTest,
            RampTest,
            FullSuiteTest,
            WatchdogTest,
        ]

        for cls in test_classes:
            assert hasattr(cls, 'get_description'), f"{cls.__name__} missing get_description"
            assert hasattr(cls, 'run'), f"{cls.__name__} missing run"
            assert issubclass(cls, BaseTest), f"{cls.__name__} should subclass BaseTest"

    def test_import_logger(self):
        """Logger module should import without error."""
        import logger
        assert hasattr(logger, 'DataLogger')

    def test_import_hal(self):
        """HAL module should import without error."""
        import hal_interface
        assert hasattr(hal_interface, 'HalInterface')
        assert hasattr(hal_interface, 'MockState')


class TestConfiguration:
    """Verify configuration values are sensible."""

    def test_monitor_pins_not_empty(self):
        """MONITOR_PINS should have required entries."""
        from config import MONITOR_PINS
        required_pins = ['feedback', 'error', 'output']
        for pin in required_pins:
            assert pin in MONITOR_PINS, f"Missing required pin: {pin}"
            assert MONITOR_PINS[pin], f"Pin mapping for {pin} is empty"

    def test_baseline_params_not_empty(self):
        """BASELINE_PARAMS should have PID values."""
        from config import BASELINE_PARAMS
        required_params = ['P', 'I', 'D']
        for param in required_params:
            assert param in BASELINE_PARAMS, f"Missing required param: {param}"

    def test_performance_targets(self):
        """Performance targets should be defined."""
        from tests.base import TARGETS
        assert TARGETS.settling_excellent > 0
        assert TARGETS.settling_good >= TARGETS.settling_excellent
        assert TARGETS.overshoot_excellent >= 0
        assert TARGETS.overshoot_good >= TARGETS.overshoot_excellent
