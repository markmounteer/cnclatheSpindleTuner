"""Tests for mock-mode HAL parameter handling."""

import pytest


def test_mock_bulk_set_clamps_and_validates(mock_hal):
    """Bulk parameter setting in mock mode should clamp and ignore unknowns."""
    # Include out-of-range values and an unknown parameter
    result = mock_hal.set_params_bulk({"P": -1.0, "Deadband": 200.0, "Unknown": 5.0})

    assert result
    # Values should be clamped to defined min/max with step snapping
    assert mock_hal.get_param("P") == 0.0
    assert mock_hal.get_param("Deadband") == 50.0


def test_mock_reverse_commands_are_signed(mock_hal):
    """Reverse MDI commands should produce negative command values in mock mode."""
    mock_hal.send_mdi("M4 S500")

    values = mock_hal.get_all_values()

    assert values["cmd_raw"] < 0
    assert values["cmd_limited"] <= 0
