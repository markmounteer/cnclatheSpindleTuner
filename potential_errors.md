# Potential Errors - Pending Verification

This file documents issues discovered during code review that require verification before correction.

---

## dashboard.py

### 1. Section Reference "§10.2" - Unknown Document Source

- **Lines**: 20, 367
- **Content**: `(§10.2)` appears in comments related to revs gauge for threading
- **Description**: The section reference §10.2 appears twice without specifying which document it references
- **Why uncertain**: May be a valid reference to external LinuxCNC documentation, hardware manual, or project-specific documentation
- **Verification needed**: Confirm whether §10.2 refers to a known document section; if not, remove or clarify the reference

### 2. Hardcoded Plot Trace Label May Not Match Defaults

- **Line**: 523
- **Content**: `self.plot_mode_label = ttk.Label(controls, text="Plot: Command, Feedback, Error, Integrator", ...)`
- **Description**: The label text is hardcoded to show four traces, but actual visible traces depend on `PLOT_DEFAULTS` from config.py
- **Why uncertain**: The label may be intentionally informational (showing available traces) rather than reflecting current state
- **Verification needed**: Check if PLOT_DEFAULTS matches this list; consider whether label should be dynamic or if current behavior is acceptable
# Potential Errors - Pending Review

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

### 2. Auto-Reconnect Claim May Be Inaccurate

- **Source file**: `hal_interface.py`
- **Line number**: 13
- **Description**: The introductory docstring lists "Connection state management with auto-reconnect" as an improvement, but the code only falls back to mock mode on connection failure and does not appear to attempt reconnection.
- **Why uncertain**: There may be reconnection logic elsewhere in the application or planned but not present in this module, so the statement could still be valid in a broader context.
- **Verification needed**: Confirm whether any automatic reconnection is implemented elsewhere or intended; if not, update the documentation to reflect the current behavior.

---

*Document generated: 2025-12-05*
*Reviewed file: hal_interface.py*
