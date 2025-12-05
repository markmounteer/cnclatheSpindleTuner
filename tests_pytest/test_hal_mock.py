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
