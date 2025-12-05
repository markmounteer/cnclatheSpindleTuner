# Potential Features Register
**Directory:** /home/user/cnclatheSpindleTuner/reference/
**Last Updated:** 2025-12-05 19:15 UTC
**Total Entries:** 6 | **New:** 6 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| FEAT-20251205-001 | New | Low | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Add read-request function documentation | 2025-12-05 |
| FEAT-20251205-002 | New | Low | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Add DPLL phase-error diagnostic net | 2025-12-05 |
| FEAT-20251205-003 | New | Low | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Document lowpass filter gain formula | 2025-12-05 |
| FEAT-20251205-004 | New | Low | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Document debounce delay units | 2025-12-05 |
| FEAT-20251205-005 | New | Medium | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Spindle safety hardening with E-stop gate | 2025-12-05 |
| FEAT-20251205-006 | New | Low | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Add at-speed relative tolerance with scale | 2025-12-05 |

---

## Entries

### FEAT-20251205-001 Add read-request function documentation

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | Section 15.2 (Mesa Configuration) or new section |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Low |
| Duplicate Of | N/A |

**Description:** Add documentation about `hm2_7i76e.0.read-request` function for HostMot2 Ethernet boards to reduce servo-thread time by overlapping request/response.

**Context:** The guide's Section 15.2 shows Mesa encoder configuration but does not mention the read-request function, which can improve performance on Ethernet boards.

**Original Agent Rationale:** "HostMot2 provides a `read-request` function specifically to reduce servo-thread time on Ethernet boards when available, by overlapping request/response." The agent references the HostMot2 man page and suggests adding `addf hm2_7i76e.0.read-request servo-thread` before `.read`.

**Evaluator Assessment:** This is a valid performance optimization suggestion. The 7i76E is an Ethernet board, so this could be beneficial. However, it requires verification that the function exists on the user's specific firmware and that it provides measurable improvement.

**Implementation Considerations:**
- Verify `halcmd show funct` shows `read-request` exists before documenting
- Add conditional guidance ("if available")
- Consider adding to Section 5 (Pre-Flight) or Section 15 (Hardware Specifications)
- Low priority as current configuration works without it

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-002 Add DPLL phase-error diagnostic net

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | Section 5.4 (DPLL Verification) |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Low |
| Duplicate Of | N/A |

**Description:** Add documentation for a DPLL phase-error diagnostic signal that can be monitored in HALShow: `net hm2-dpll-phase-error hm2_7i76e.0.dpll.phase-error-us`

**Context:** Section 5.4 already shows how to verify DPLL configuration and monitor phase error with `watch` command, but doesn't suggest creating a named signal for easier HALShow monitoring.

**Original Agent Rationale:** Agent suggests "Add a diagnostic net for phase error so you can watch it in HALShow" and notes that timer-number latching "should typically be enabled" for reduced following errors.

**Evaluator Assessment:** This is a minor convenience enhancement. The guide already shows `watch -n 0.5 "halcmd show param hm2_7i76e.0.dpll.phase-error-us"` in Section 5.4, which accomplishes the same monitoring goal. A named net would make HALShow access slightly easier but is not essential.

**Implementation Considerations:**
- Could add one line to Section 5.4 verification steps
- Very low implementation effort
- Minimal documentation value as alternative already shown
- Consider whether adding more signals adds complexity

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-003 Document lowpass filter gain formula

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | Section 4.2 (Feedback Path) or new subsection |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Low |
| Duplicate Of | N/A |

**Description:** Document the mathematical relationship between lowpass filter gain and the intended cutoff frequency: `gain = 1 - exp(-a*T)` where `a` is the pole in rad/s and `T` is the sample period.

**Context:** Section 4.2 mentions "lowpass filter (smoothing, gain=0.5)" but does not explain how this gain value relates to cutoff frequency or servo period.

**Original Agent Rationale:** "LinuxCNC documents how `lowpass.gain` relates to the continuous pole and sampling period." Agent suggests recording the intended cutoff and servo period used to compute the FILTER_GAIN parameter for future tuning.

**Evaluator Assessment:** This would add educational value for users who want to understand or adjust the filter. However, for a practical tuning guide, gain=0.5 works well and most users don't need the underlying math. Could be added as an optional advanced note.

**Implementation Considerations:**
- Could add a brief formula note in Section 4.2 or as an appendix
- Risk of overcomplicating a practical tuning guide
- Most users adjust gain empirically, not mathematically
- Consider adding as "Advanced" or "For reference" note

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-004 Document debounce delay units

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | New section or relevant configuration section |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Low |
| Duplicate Of | N/A |

**Description:** Add documentation explaining that `debounce` component delay is specified in servo-thread cycles (iterations), not milliseconds. Suggest adding a comment like: "debounce.0.delay is in servo cycles (delay * SERVO_PERIOD seconds)"

**Context:** The guide does not currently discuss debounce configuration. If debounce is used in the system's HAL files, users may not realize the delay value is cycle-based.

**Original Agent Rationale:** Agent references LinuxCNC debounce man page noting that delay is "counter-based and the 'delay' is effectively in servo-thread iterations, not milliseconds."

**Evaluator Assessment:** This is a valid clarification if debounce is used in the system. However, the current guide does not appear to cover debounce settings. This would be a new addition rather than clarification of existing content.

**Implementation Considerations:**
- First verify if debounce is actually used in this system's HAL configuration
- If used, add brief explanation to relevant section
- Low priority as guide focuses on spindle PID, not general HAL components
- Could be added if guide is expanded to cover all HAL components

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-005 Spindle safety hardening with E-stop gate

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | Section 13 (Commissioning Cleanup) or Section 6 (Safety) |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Medium |
| Duplicate Of | N/A |

**Description:** Add safety hardening recommendations including:
1. Gate spindle enable with the E-stop chain so VFD run signal cannot stay asserted if `external-ok` drops
2. Consider resetting the speed filter when spindle is disabled to prevent stale filtered values

**Context:** The guide covers E-stop testing in Section 6.3 and safety validation in Section 13.3, but does not explicitly recommend gating spindle enable with the E-stop chain in HAL.

**Original Agent Rationale:** Agent suggests "Gate spindle enable with your estop chain, not just spindle.0.on, so the VFD run signal can't ever stay asserted if external-ok drops." Also suggests resetting speed filter on spindle disable.

**Evaluator Assessment:** This is a reasonable safety enhancement. Gating spindle enable with external-ok adds defense-in-depth. The current guide assumes proper E-stop wiring but doesn't explicitly document this pattern. Medium priority as it relates to safety.

**Implementation Considerations:**
- Would add complexity to HAL configuration
- Should verify current system behavior with E-stop
- Could add to Section 13.3 Safety Validation as best practice
- Filter reset suggestion needs careful consideration (could affect at-speed behavior)

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-006 Add at-speed relative tolerance with scale

| Field | Value |
|-------|-------|
| Status | New |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | Section 10.2 (Threading-Specific Settings) |
| Submitted By | External AI Agent (ChatGPT) |
| Evaluated By | Claude (claude-opus-4-5-20251101) |
| Submitted | 2025-12-05 |
| Priority | Low |
| Duplicate Of | N/A |

**Description:** Document the `near` component's `scale` parameter for at-speed detection. Currently using absolute `difference` only; could use `scale` for relative tolerance (e.g., "plus or minus X% at high RPM but at least plus or minus Y RPM").

**Context:** Section 14.1 shows `AT_SPEED_TOLERANCE = 20` (absolute RPM). The `near` component supports both absolute difference AND scale factor with OR logic.

**Original Agent Rationale:** Agent notes that `near` "asserts true if values are within a scale factor OR an absolute difference" and suggests trying `scale=1.02` with a small absolute difference for combined behavior.

**Evaluator Assessment:** This is a valid enhancement for users who want percentage-based tolerance at higher speeds. The current absolute tolerance (20 RPM) works for most use cases. Adding scale adds complexity and requires understanding the OR logic behavior.

**Implementation Considerations:**
- Current absolute tolerance is simple and works well
- Percentage tolerance more relevant at high RPM (20 RPM is 1% at 2000 RPM, 4% at 500 RPM)
- Would need to explain OR logic behavior clearly
- Could add as "Advanced" option in Section 10.2

**Review History:**
- 2025-12-05 | External AI Agent | Submitted feature suggestion.
- 2025-12-05 | Claude | Evaluated as feature suggestion; added to register.

---
