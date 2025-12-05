from hal_interface import HalInterface


def test_set_params_bulk_invalid_value_does_not_apply():
    """Invalid parameter values in mock mode should not be reported as applied."""

    hal = HalInterface(mock=True)

    baseline_p = hal.mock_state.params["P"]

    # Provide a non-numeric value; previous behavior reported success despite no update.
    result = hal.set_params_bulk({"P": "not-a-number"})

    assert result is False
    assert hal.mock_state.params["P"] == baseline_p
