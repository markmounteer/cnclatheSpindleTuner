# Potential Errors Register
**Last Updated:** 2025-12-05 12:00 UTC
**Total Entries:** 4 | **New:** 4 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| ERR-20251205-001 | 🆕 New | 🟡 Medium | `/dashboard.py` | Section Reference "§10.2" - Unknown Document Source | 2025-12-05 |
| ERR-20251205-002 | 🆕 New | 🟢 Low | `/dashboard.py` | Hardcoded Plot Trace Label May Not Match Defaults | 2025-12-05 |
| ERR-20251205-003 | 🆕 New | 🟢 Low | `/hal_interface.py` | Tuning Guide Version Reference May Be Outdated | 2025-12-05 |
| ERR-20251205-004 | 🆕 New | 🟡 Medium | `/hal_interface.py` | Auto-Reconnect Claim May Be Inaccurate | 2025-12-05 |

---

## Entries

### dashboard.py

---

### ERR-20251205-001 Section Reference "§10.2" - Unknown Document Source

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/dashboard.py` |
| Location | Lines 20, 367 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | — |

**Description:**
The section reference §10.2 appears twice in comments related to revs gauge for threading without specifying which document it references.

**Context:**
`(§10.2)` appears in comments at lines 20 and 367 related to revs gauge for threading.

**Rationale:**
May be a valid reference to external LinuxCNC documentation, hardware manual, or project-specific documentation, but without clarification readers cannot verify or follow up on the reference.

**Verification Required:**
Confirm whether §10.2 refers to a known document section; if not, remove or clarify the reference.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### ERR-20251205-002 Hardcoded Plot Trace Label May Not Match Defaults

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
The label text is hardcoded to show four traces ("Command, Feedback, Error, Integrator"), but actual visible traces depend on `PLOT_DEFAULTS` from config.py.

**Context:**
```python
self.plot_mode_label = ttk.Label(controls, text="Plot: Command, Feedback, Error, Integrator", ...)
```

**Rationale:**
The label may be intentionally informational (showing available traces) rather than reflecting current state, but this creates potential confusion if `PLOT_DEFAULTS` differs from the displayed text.

**Verification Required:**
Check if PLOT_DEFAULTS matches this list; consider whether label should be dynamic or if current behavior is acceptable.

**Related Entries:**
- See FEAT-20251205-002 for proposed enhancement to make this label dynamic.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### hal_interface.py

---

### ERR-20251205-003 Tuning Guide Version Reference May Be Outdated

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/hal_interface.py` |
| Location | Line 1628 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | — |

**Description:**
The comment references "Spindle PID Tuning Guide v5.3" in the generated INI section, but the guide version number may have been updated since this code was written. The CHANGELOG references "Spindle Tuner v6.0" but there's no clear indication of what the current tuning guide version should be.

**Context:**
```python
"# Based on Spindle PID Tuning Guide v5.3",
```

**Rationale:**
Outdated version references in generated configuration files may cause confusion for users trying to locate the correct documentation version.

**Verification Required:**
Confirm the current version of the Spindle PID Tuning Guide documentation and update the reference if outdated.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

### ERR-20251205-004 Auto-Reconnect Claim May Be Inaccurate

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | `/hal_interface.py` |
| Location | Line 13 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | — |

**Description:**
The introductory docstring lists "Connection state management with auto-reconnect" as an improvement, but the code only falls back to mock mode on connection failure and does not appear to attempt reconnection.

**Context:**
Module docstring at line 13 claims auto-reconnect capability that may not be implemented.

**Rationale:**
Documentation claiming functionality that doesn't exist can mislead developers and users. There may be reconnection logic elsewhere in the application or planned but not present in this module.

**Verification Required:**
Confirm whether any automatic reconnection is implemented elsewhere or intended; if not, update the documentation to reflect the current behavior.

**Related Entries:**
- See FEAT-20251205-008 for proposed enhancement to implement optional HAL reconnection attempts.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format

---

## Archive

*No resolved entries yet.*
