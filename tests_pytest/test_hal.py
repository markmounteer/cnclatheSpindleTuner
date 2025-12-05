"""Unit tests for HAL helper behaviors and mock physics."""

import math
import time

import pytest

from hal_interface import HalInterface


def test_clamp_and_snap_respects_range():
    """Values should be clamped to min/max and snapped to the nearest step."""
    assert HalInterface._clamp_and_snap(1.234, 0.0, 2.0, 0.1) == pytest.approx(1.2)
    assert HalInterface._clamp_and_snap(-5.0, 0.0, 1.0, 0.5) == 0.0
    assert HalInterface._clamp_and_snap(5.0, 0.0, 1.0, 0.01) == 1.0


def test_set_param_snaps_and_clamps(mock_hal):
    """set_param should enforce tuning parameter ranges in mock mode."""
    assert mock_hal.set_param("P", 5.0)
    assert mock_hal.mock_state.params["P"] == 1.0  # max value from TUNING_PARAMS

    assert mock_hal.set_param("RateLimit", 1125.0)
    # RateLimit step is 50; 1125 rounds to 1100
    assert mock_hal.mock_state.params["RateLimit"] == 1100.0

    assert not mock_hal.set_param("UNKNOWN", 1.0)


def test_parse_hal_value_handles_booleans_and_nan():
    """Boolean strings should coerce to floats; NaN should raise."""
    assert HalInterface._parse_hal_value("TRUE") == 1.0
    assert HalInterface._parse_hal_value("off") == 0.0

    with pytest.raises(ValueError):
        HalInterface._parse_hal_value("nan")


def test_mock_rate_limit_slow_start(mock_hal):
    """Mock physics should respect the configured rate limit during acceleration."""
    mock_hal.mock_state.params["RateLimit"] = 100.0
    engine = mock_hal._physics_engine

    # Force a controlled timestep for deterministic max_change
    engine._last_update_mono = time.monotonic() - 0.1
    mock_hal.mock_state.cmd = 500.0
    mock_hal.mock_state.limited_cmd = 0.0

    values = engine.update()
    max_expected = mock_hal.mock_state.params["RateLimit"] * 0.1
    limited = values["spindle-vel-cmd-rpm-limited"]

    # Allow a small tolerance because the simulated timestep is based on monotonic clock
    assert 0 < limited <= max_expected * 1.02
    assert math.isclose(mock_hal.mock_state.limited_cmd, limited, rel_tol=1e-6)
