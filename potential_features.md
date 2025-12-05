# Potential Features - Enhancement Suggestions

This document tracks improvements and enhancements identified during code review. These are suggestions only and should not be implemented without explicit approval.

---

## logger.py

### 1. Extract Duplicate `_get_value` Helper to Class Method

- **Current state**: The `_get_value` helper function is defined as a nested function twice - once in `calculate_step_metrics()` (lines 278-281) and once in `calculate_load_metrics()` (lines 403-413). The implementations are similar but not identical.
- **Suggested enhancement**: Factor out to a single `@staticmethod` or instance method like `_extract_value(point, key, default)` that handles dict, tuple/list, and object attribute access uniformly.
- **Rationale**: Reduces code duplication (DRY principle), ensures consistent behavior, and makes the helper testable independently.
- **Implementation considerations**: The two versions have slightly different signatures (one uses string keys, one uses integer indices). A unified version would need to handle both cases, possibly using `Union[str, int]` for the key type.

### 2. Reuse `clear_buffers()` in `clear_recording()`

- **Current state**: The `clear_recording()` method (lines 158-167) attempts to clear buffers individually, while `clear_buffers()` (lines 151-156) already provides correct buffer clearing logic.
- **Suggested enhancement**: After fixing the bug in `clear_recording()`, consider calling `self.clear_buffers()` instead of duplicating buffer-clearing code.
- **Rationale**: Reduces maintenance burden and ensures both methods stay synchronized if buffer structure changes.
- **Implementation considerations**: Evaluate whether `clear_recording()` should always clear plot buffers or if there are use cases where recording should be cleared but plot buffers preserved. If the latter, keep them separate.

### 3. Add Input Validation Logging

- **Current state**: The `_safe_float()` method (lines 102-107) silently returns a default value when conversion fails.
- **Suggested enhancement**: Optionally log a debug message when conversion fails to aid troubleshooting data quality issues.
- **Rationale**: Silent failures can mask upstream data problems. Debug logging would help identify callers passing unexpected data types.
- **Implementation considerations**: Should be debug-level logging only to avoid noise. Consider adding a class-level flag to enable/disable this logging.

### 4. Add Type Hints for `test_data` Parameter

- **Current state**: `calculate_step_metrics()` accepts `test_data: List[Any]` (line 253) which is very permissive.
- **Suggested enhancement**: Define a `Protocol` or `TypedDict` describing the expected structure (must have `relative_time`, `feedback`, `error` attributes/keys).
- **Rationale**: Improves IDE support, catches type errors earlier, and documents the expected input format.
- **Implementation considerations**: The current implementation handles both dict and object inputs, so a `Union` type or `Protocol` would be needed rather than a simple `TypedDict`.
This document contains potential improvements identified during code review that could benefit the codebase.

---

## hal_interface.py

### 1. Add `__all__` Export List

- **Source file**: `hal_interface.py`
- **Current state**: The module does not define an `__all__` list, making the public API implicit.
- **Suggested enhancement**: Add an explicit `__all__` list to document the public API:
  ```python
  __all__ = [
      'ConnectionState',
      'SpindleDirection',
      'CachedValue',
      'MockState',
      'PhysicsParameters',
      'MockPhysicsEngine',
      'HalInterface',
      'IniFileHandler',
      'IS_WINDOWS',
      'IS_LINUX',
      'HAS_HALCMD',
      'HAS_LINUXCNC',
  ]
  ```
- **Rationale**: Explicit exports improve code documentation, IDE autocompletion, and help prevent accidental use of internal functions. This follows the pattern used in config.py.
- **Implementation considerations**: Low risk, purely additive change. Should be placed after the imports section.

### 2. Add Type Annotations for Imported Configuration Constants

- **Source file**: `hal_interface.py`
- **Current state**: Lines 37-40 import `MONITOR_PINS`, `TUNING_PARAMS`, `BASELINE_PARAMS`, `UPDATE_INTERVAL_MS`, `MOTOR_SPECS`, and `VFD_SPECS` without local type annotations.
- **Suggested enhancement**: Add type comments or use explicit type annotations to document the expected types:
  ```python
  from config import (
      MONITOR_PINS,      # Dict[str, str]
      TUNING_PARAMS,     # Dict[str, TuningParamSpec]
      BASELINE_PARAMS,   # Dict[str, float]
      UPDATE_INTERVAL_MS,  # int
      MOTOR_SPECS,       # Dict[str, Any]
      VFD_SPECS          # Dict[str, Any]
  )
  ```
- **Rationale**: Improves code readability and helps developers understand the data structures being used without needing to reference config.py.
- **Implementation considerations**: Low risk. Can be done as type comments (as shown) or by creating type aliases in the module.

---

*Document generated: 2025-12-05*
*Reviewed file: hal_interface.py*
