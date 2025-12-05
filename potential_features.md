# Potential Features Register
**Last Updated:** 2025-12-05 12:00 UTC
**Total Entries:** 8 | **New:** 8 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| FEAT-20251205-001 | 🆕 New | 🟢 Low | `/dashboard.py` | Error History Export | 2025-12-05 |
| FEAT-20251205-002 | 🆕 New | 🟢 Low | `/dashboard.py` | Speed Entry Field Validation | 2025-12-05 |
| FEAT-20251205-003 | 🆕 New | 🟢 Low | `/dashboard.py` | Dynamic Plot Trace Label | 2025-12-05 |
| FEAT-20251205-004 | 🆕 New | 🟢 Low | `/dashboard.py` | Fallback Chart Error Trace Scaling Indicator | 2025-12-05 |
| FEAT-20251205-005 | 🆕 New | 🟢 Low | `/dashboard.py` | Keyboard Shortcut Help Overlay | 2025-12-05 |
| FEAT-20251205-006 | 🆕 New | 🟢 Low | `/hal_interface.py` | Add Type Annotations for Imported Configuration Constants | 2025-12-05 |
| FEAT-20251205-007 | 🆕 New | 🟢 Low | `/hal_interface.py` | Add `__all__` Export List | 2025-12-05 |
| FEAT-20251205-008 | 🆕 New | 🟡 Medium | `/hal_interface.py` | Implement Optional HAL Reconnection Attempts | 2025-12-05 |

---

## Entries

### dashboard.py

---

### FEAT-20251205-001 Error History Export

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Lines 404–430 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add option to export raw error history data for external analysis.

**Context:**
Statistics panel (lines 404-430) tracks error history but only displays aggregated stats.

**Rationale:**
Advanced users may want to perform custom analysis on error patterns. Exporting raw data would enable use of external tools for deeper statistical analysis.

**Implementation Considerations:**
- Could add export button to stats panel
- Consider memory implications of larger history buffers
- Format options: CSV, JSON, or plain text
- May need to limit export size or add pagination for large histories

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-002 Speed Entry Field Validation

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Line 441 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add input validation to prevent non-numeric characters from being entered in the speed entry field.

**Context:**
Line 441 - Speed entry accepts any text input; validation only happens when attempting to convert to int (lines 1266-1269, 1280-1281).

**Rationale:**
Would provide immediate feedback to users rather than silently failing or defaulting to 1000 RPM.

**Implementation Considerations:**
- Could use `validatecommand` with `%P` substitution or bind to `KeyRelease` events
- Need to consider paste operations
- Should handle edge cases like empty input, leading zeros, negative values

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-003 Dynamic Plot Trace Label

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Line 523 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Update the plot mode label dynamically based on which traces are actually visible.

**Context:**
Line 523 - Plot mode label is hardcoded to "Plot: Command, Feedback, Error, Integrator".

**Rationale:**
Would accurately reflect current plot state and help users understand what they're viewing.

**Implementation Considerations:**
- Would need to update label in `_update_trace_visibility()` method
- Consider performance if called frequently
- Label length may vary; ensure UI can accommodate different lengths

**Related Entries:**
- See ERR-20251205-002 for the related error entry about hardcoded label mismatch.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-004 Fallback Chart Error Trace Scaling Indicator

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Lines 1016–1020 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add a separate Y-axis or legend indicator for error scale in fallback mode.

**Context:**
Lines 1016-1020 - Error trace is scaled by 5x and centered at 1000 RPM for visibility in the canvas fallback chart.

**Rationale:**
The current 5x scaling may confuse users who don't realize error values are magnified.

**Implementation Considerations:**
- Would require additional canvas elements
- Need to maintain simplicity for systems without matplotlib
- Could use a small legend or annotation rather than a full secondary axis

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-005 Keyboard Shortcut Help Overlay

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Lines 1143–1156 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add a help button or tooltip that shows available keyboard shortcuts.

**Context:**
Lines 1143-1156 - Keyboard shortcuts exist (Space=stop, F5=step test, 1-4=speed presets) but are only documented in module docstring.

**Rationale:**
Discoverability - users may not know these shortcuts exist.

**Implementation Considerations:**
- Could be a simple button that shows a messagebox or tooltip
- Minimal code addition
- Consider adding a "?" button in the toolbar or a Help menu item

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### hal_interface.py

---

### FEAT-20251205-006 Add Type Annotations for Imported Configuration Constants

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/hal_interface.py` |
| Location | Lines 37–40 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add type comments or use explicit type annotations to document the expected types of imported configuration constants.

**Context:**
Lines 37-40 import `MONITOR_PINS`, `TUNING_PARAMS`, `BASELINE_PARAMS`, `UPDATE_INTERVAL_MS`, `MOTOR_SPECS`, and `VFD_SPECS` without local type annotations.

**Rationale:**
Improves code readability and helps developers understand the data structures being used without needing to reference config.py.

**Implementation Considerations:**
- Low risk, purely additive change
- Can be done as type comments or by creating type aliases in the module
- Example:
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

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-007 Add `__all__` Export List

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/hal_interface.py` |
| Location | After imports section |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
Add an explicit `__all__` list to document the public API.

**Context:**
The module does not define an `__all__` list, making the public API implicit.

**Rationale:**
Explicit exports improve code documentation, IDE autocompletion, and help prevent accidental use of internal functions. This follows the pattern used in config.py.

**Implementation Considerations:**
- Low risk, purely additive change
- Should be placed after the imports section
- Suggested contents:
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

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### FEAT-20251205-008 Implement Optional HAL Reconnection Attempts

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/hal_interface.py` |
| Location | Module-level (connection handling) |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | — |

**Description:**
Add configurable reconnection attempts with backoff before switching to mock mode, and optionally allow periodic reconnection checks while in mock fallback.

**Context:**
On failed halcmd verification, the interface falls back to mock mode without retrying a real HAL connection.

**Rationale:**
Helps maintain real hardware control when transient connectivity issues occur, aligning behavior with the stated auto-reconnect improvement in the module docstring.

**Implementation Considerations:**
- Add retry counters and delays configurable via settings
- Ensure thread safety around connection state transitions
- Avoid blocking critical paths by running retries in a background thread or using non-blocking checks

**Related Entries:**
- See ERR-20251205-004 for the related error entry about the auto-reconnect documentation claim.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

## Archive

*No resolved entries yet.*
