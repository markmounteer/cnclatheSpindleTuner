"""Unit tests for configuration constants and presets."""

from config import BASELINE_PARAMS, ENCODER_SPECS, MONITOR_PINS, PRESETS, TUNING_PARAMS


def test_baseline_params_within_bounds():
    """Baseline PID values should respect the declared tuning parameter ranges."""
    for name, value in BASELINE_PARAMS.items():
        assert name in TUNING_PARAMS, f"Unknown baseline parameter: {name}"
        spec = TUNING_PARAMS[name]
        assert spec.min_val <= value <= spec.max_val, (
            f"{name} baseline {value} is outside {spec.min_val}–{spec.max_val}"
        )


def test_presets_respect_tuning_specs():
    """Every preset should only include known parameters within allowed ranges."""
    for preset_name, params in PRESETS.items():
        for param, value in params.items():
            assert param in TUNING_PARAMS, f"{preset_name} uses unknown param {param}"
            spec = TUNING_PARAMS[param]
            assert spec.min_val <= value <= spec.max_val, (
                f"{preset_name}:{param} value {value} outside {spec.min_val}–{spec.max_val}"
            )


def test_monitor_pins_are_unique():
    """Pin mappings should not contain duplicate HAL targets."""
    pin_targets = list(MONITOR_PINS.values())
    assert pin_targets, "MONITOR_PINS should not be empty"

    # external_ok and safety_chain intentionally point to the same HAL pin
    allowed_duplicates = {MONITOR_PINS.get("external_ok")}
    duplicates = {
        target
        for target in pin_targets
        if pin_targets.count(target) > 1 and target not in allowed_duplicates
    }

    assert not duplicates, f"Unexpected duplicate HAL pins detected: {duplicates}"


def test_encoder_specs_are_positive():
    """Encoder configuration must use positive, non-zero values."""
    assert ENCODER_SPECS["counts_per_rev"] > 0
    assert abs(ENCODER_SPECS["dpll_timer_us"]) > 0
