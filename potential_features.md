# Potential Features Register
**Directory:** /workspace/cnclatheSpindleTuner/
**Last Updated:** 2025-12-05 18:13 UTC
**Total Entries:** 8 | **New:** 8 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| FEAT-20251205-001 | 🆕 New | 🟢 Low | dashboard.py | Error History Export | 2025-12-05 |
| FEAT-20251205-002 | 🆕 New | 🟢 Low | dashboard.py | Speed Entry Field Validation | 2025-12-05 |
| FEAT-20251205-003 | 🆕 New | 🟢 Low | dashboard.py | Dynamic Plot Trace Label | 2025-12-05 |
| FEAT-20251205-004 | 🆕 New | 🟢 Low | dashboard.py | Fallback Chart Error Trace Scaling Indicator | 2025-12-05 |
| FEAT-20251205-005 | 🆕 New | 🟢 Low | dashboard.py | Keyboard Shortcut Help Overlay | 2025-12-05 |
| FEAT-20251205-006 | 🆕 New | 🟢 Low | hal_interface.py | Add Type Annotations for Imported Configuration Constants | 2025-12-05 |
| FEAT-20251205-007 | 🆕 New | 🟢 Low | hal_interface.py | Add `__all__` Export List | 2025-12-05 |
| FEAT-20251205-008 | 🆕 New | 🟡 Medium | hal_interface.py | Implement Optional HAL Reconnection Attempts | 2025-12-05 |

---

## Entries

### FEAT-20251205-001 Error History Export

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Lines 404–430 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add an option to export raw error history data for external analysis.

**Context:** The statistics panel tracks error history but only displays aggregated metrics.

**Rationale:** Exporting raw data would let advanced users perform custom analysis with external tools.

**Implementation Considerations:**
- Add an export control to the statistics panel.
- Choose formats such as CSV, JSON, or plain text.
- Manage memory for large history buffers and consider limits on export size.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-002 Speed Entry Field Validation

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Line 441 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add input validation to prevent non-numeric characters in the speed entry field.

**Context:** Validation currently occurs only when converting input to an integer during use.

**Rationale:** Immediate feedback would reduce confusion and prevent silent fallback to default speeds.

**Implementation Considerations:**
- Use `validatecommand` or event bindings to restrict input.
- Handle paste operations and empty input gracefully.
- Decide how to treat negatives and leading zeros.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-003 Dynamic Plot Trace Label

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Line 523 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Update the plot mode label dynamically based on which traces are visible.

**Context:** The plot label is currently hardcoded to list four traces.

**Rationale:** A dynamic label would reflect the active traces and reduce confusion.

**Implementation Considerations:**
- Update the label within `_update_trace_visibility()` or equivalent logic.
- Ensure the UI can accommodate varying label lengths.
- Consider performance if updates occur frequently.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-004 Fallback Chart Error Trace Scaling Indicator

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Lines 1016–1020 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add a Y-axis indicator or legend note that the error trace is scaled in fallback mode.

**Context:** The canvas fallback chart scales error by 5x and centers it for visibility without disclosing the scaling.

**Rationale:** Users may misinterpret magnified error values without a visible scaling note.

**Implementation Considerations:**
- Add a small legend annotation rather than a full secondary axis.
- Keep the canvas display simple for environments without matplotlib.
- Ensure the indicator does not clutter the existing layout.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-005 Keyboard Shortcut Help Overlay

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Lines 1143–1156 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Provide an in-app overlay summarizing available keyboard shortcuts.

**Context:** Shortcuts are handled in code but not documented within the UI.

**Rationale:** Visible shortcut help would improve discoverability and usability.

**Implementation Considerations:**
- Add a help dialog or tooltip listing shortcuts and actions.
- Ensure the overlay is accessible without conflicting with existing shortcuts.
- Keep the overlay optional to avoid clutter.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-006 Add Type Annotations for Imported Configuration Constants

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Multiple references |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add explicit type annotations for configuration constants imported from `config.py`.

**Context:** Constants are used throughout the module without annotations, which can reduce type checker clarity.

**Rationale:** Explicit types would aid static analysis and documentation.

**Implementation Considerations:**
- Import `Final` or explicit types for shared constants.
- Ensure annotations stay synchronized with `config.py` definitions.
- Keep runtime behavior unchanged.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-007 Add `__all__` Export List

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Module scope |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Define `__all__` to clarify the public API of `hal_interface.py`.

**Context:** The module currently exports everything by default.

**Rationale:** An explicit export list would communicate supported symbols and aid tooling.

**Implementation Considerations:**
- Enumerate public classes, functions, and constants in `__all__`.
- Keep backward compatibility for consumers relying on implicit exports.
- Update documentation if necessary.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### FEAT-20251205-008 Implement Optional HAL Reconnection Attempts

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Connection handling |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** Attempt HAL reconnection a configurable number of times before falling back to mock mode.

**Context:** On connection failure the module immediately switches to mock mode without retries.

**Rationale:** Limited retry attempts could recover from transient issues while retaining the mock fallback.

**Implementation Considerations:**
- Add configurable retry count and delay.
- Ensure retries do not block the UI excessively.
- Preserve the existing mock fallback path when retries are exhausted.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---
