# Potential Errors - Pending Review

This document tracks issues that require verification before correction.

---

## logger.py

### 1. at_speed Numeric-to-Boolean Conversion

- **Line number**: 139
- **Description**: The expression `at_speed=values.get("at_speed", 0.0) > 0.5` assumes the "at_speed" value from the input dict is always numeric. If callers sometimes pass a boolean value directly, the comparison `True > 0.5` evaluates to `True` (since `True == 1`), but `False > 0.5` evaluates to `False` - this happens to work correctly, but the intent is unclear.
- **Why uncertain**: The code functions correctly for both numeric and boolean inputs due to Python's boolean-to-int coercion, but it's unclear whether this was intentional or accidental. Need to verify the expected input type from all callers.
- **Verification needed**: Review all call sites that pass "at_speed" values to `add_sample()` to confirm whether the value is always numeric (0.0/1.0) or sometimes boolean.

### 2. Silent Config Guard May Mask Errors

- **Line number**: 82
- **Description**: The guard `interval_ms = UPDATE_INTERVAL_MS if UPDATE_INTERVAL_MS > 0 else 1` silently defaults to 1ms if `UPDATE_INTERVAL_MS` is zero or negative. This prevents division-by-zero but could mask a configuration error.
- **Why uncertain**: This defensive coding may be intentional to ensure robustness, or it may hide legitimate configuration mistakes that should raise an error. The project's error handling philosophy is unclear.
- **Verification needed**: Determine if config.py guarantees `UPDATE_INTERVAL_MS > 0` and whether silent fallback is preferred over raising a `ValueError`.
This document contains potential issues identified during code review that require verification before fixing.

---

## hal_interface.py

### 1. Tuning Guide Version Reference May Be Outdated

- **Source file**: `hal_interface.py`
- **Line number**: 1628
- **Description**: The comment references "Spindle PID Tuning Guide v5.3" in the generated INI section
- **Current text**: `"# Based on Spindle PID Tuning Guide v5.3",`
- **Why uncertain**: The guide version number may have been updated since this code was written. The CHANGELOG references "Spindle Tuner v6.0" but there's no clear indication of what the current tuning guide version should be.
- **Verification needed**: Confirm the current version of the Spindle PID Tuning Guide documentation and update the reference if outdated.

---

*Document generated: 2025-12-05*
*Reviewed file: hal_interface.py*
