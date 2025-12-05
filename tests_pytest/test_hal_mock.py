"""Tests for mock-mode HAL parameter handling."""

from hal import HalInterface


def test_mock_bulk_set_clamps_and_validates():
    """Bulk parameter setting in mock mode should clamp and ignore unknowns."""

    hal = HalInterface(mock=True)

    # Include out-of-range values and an unknown parameter
    result = hal.set_params_bulk({"P": -1.0, "Deadband": 200.0, "Unknown": 5.0})

    assert result is True
    # Values should be clamped to defined min/max with step snapping
    assert hal.get_param("P") == 0.0
    assert hal.get_param("Deadband") == 50.0


def test_mock_reverse_commands_are_signed(mock_hal):
    """Reverse MDI commands should produce negative command values in mock mode."""
    mock_hal.send_mdi("M4 S500")

    values = mock_hal.get_all_values()

    assert values["cmd_raw"] < 0
    assert values["cmd_limited"] <= 0
