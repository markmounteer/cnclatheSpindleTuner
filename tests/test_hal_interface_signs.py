import time

from hal_interface import HalInterface, SpindleDirection


def test_mock_feedback_and_error_signs():
    """Reverse rotation should produce negative feedback and error outputs."""
    hal = HalInterface(mock=True)

    with hal._lock:  # Access internal state for deterministic setup
        state = hal.mock_state
        state.direction = SpindleDirection.REVERSE
        state.cmd = 500.0
        state.limited_cmd = 500.0
        state.rpm = 250.0
        state.rpm_filtered = 250.0
        # Keep the physics step small to avoid large state changes during the test
        hal._physics_engine._last_update_mono = time.monotonic()

    outputs = hal._physics_engine.update()

    assert outputs["pid.s.feedback"] < 0
    assert outputs["pid.s.error"] < 0
    assert outputs["pid.s.feedback_raw"] == outputs["pid.s.feedback"]
