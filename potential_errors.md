# Potential Errors Register
**Directory:** /workspace/cnclatheSpindleTuner/
**Last Updated:** 2025-12-05 18:13 UTC
**Total Entries:** 4 | **New:** 4 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| ERR-20251205-001 | 🆕 New | 🟡 Medium | dashboard.py | Section Reference "§10.2" - Unknown Document Source | 2025-12-05 |
| ERR-20251205-002 | 🆕 New | 🟢 Low | dashboard.py | Hardcoded Plot Trace Label May Not Match Defaults | 2025-12-05 |
| ERR-20251205-003 | 🆕 New | 🟢 Low | hal_interface.py | Tuning Guide Version Reference May Be Outdated | 2025-12-05 |
| ERR-20251205-004 | 🆕 New | 🟡 Medium | hal_interface.py | Auto-Reconnect Claim May Be Inaccurate | 2025-12-05 |

---

## Entries

### ERR-20251205-001 Section Reference "§10.2" - Unknown Document Source

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Lines 20, 367 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** The section reference §10.2 appears twice in comments related to the revs gauge for threading without citing the referenced document.

**Context:** `(§10.2)` appears in comments at lines 20 and 367 related to the threading revs gauge.

**Rationale:** Without identifying the source document, readers cannot verify or follow up on the reference.

**Uncertainty:** The reference may correspond to a known manual section, but this is not stated explicitly.

**Verification Required:** Confirm whether §10.2 maps to a published document; if not, clarify or remove the reference.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### ERR-20251205-002 Hardcoded Plot Trace Label May Not Match Defaults

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | dashboard.py |
| Location | Line 523 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** The label text is hardcoded to show four traces ("Command, Feedback, Error, Integrator"), but actual visible traces depend on `PLOT_DEFAULTS` from `config.py`.

**Context:** The plot mode label is set statically while `PLOT_DEFAULTS` controls which traces display.

**Rationale:** Hardcoded text may misrepresent active traces, potentially confusing users.

**Uncertainty:** If the label is intended to list available traces rather than active ones, the current behavior might be acceptable.

**Verification Required:** Compare `PLOT_DEFAULTS` to the label and decide whether the label should be dynamic.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### ERR-20251205-003 Tuning Guide Version Reference May Be Outdated

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Line 1628 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** The generated INI section references "Spindle PID Tuning Guide v5.3", which may not match the current documentation version.

**Context:** Comment in the generated INI template references the tuning guide version.

**Rationale:** Outdated version references can mislead users seeking the correct documentation.

**Uncertainty:** The guide may still be at v5.3; confirmation is needed.

**Verification Required:** Check the latest tuning guide version and update the reference if necessary.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---

### ERR-20251205-004 Auto-Reconnect Claim May Be Inaccurate

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Line 13 |
| Submitted By | Code Review Agent |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** The module docstring lists "Connection state management with auto-reconnect" as an improvement, but the code only falls back to mock mode on connection failure.

**Context:** Introductory docstring claim at the top of the file.

**Rationale:** Claiming unimplemented auto-reconnect behavior can mislead developers and users.

**Uncertainty:** Auto-reconnect could be implemented elsewhere in the application; verification is required.

**Verification Required:** Determine whether automatic reconnection is implemented or intended; adjust documentation accordingly.

**Review History:**
- 2025-12-05 | System | Entry migrated to standardized register format.

---
