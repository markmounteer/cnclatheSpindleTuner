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
