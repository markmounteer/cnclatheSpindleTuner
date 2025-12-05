# Potential Features - Enhancement Suggestions

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

### 3. Implement Optional HAL Reconnection Attempts

- **Source file**: `hal_interface.py`
- **Current state**: On failed halcmd verification, the interface falls back to mock mode without retrying a real HAL connection.
- **Suggested enhancement**: Add configurable reconnection attempts with backoff before switching to mock mode, and optionally allow periodic reconnection checks while in mock fallback.
- **Rationale**: Helps maintain real hardware control when transient connectivity issues occur, aligning behavior with the stated auto-reconnect improvement in the module docstring.
- **Implementation considerations**: Add retry counters and delays configurable via settings; ensure thread safety around connection state transitions; avoid blocking critical paths by running retries in a background thread or using non-blocking checks.

---

*Document generated: 2025-12-05*
*Reviewed file: hal_interface.py*
