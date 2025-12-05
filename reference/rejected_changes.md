# Rejected Changes Register
**Directory:** /home/user/cnclatheSpindleTuner/reference/
**Last Updated:** 2025-12-05 19:15 UTC
**Total Entries:** 1

## Summary Index
| ID | Original ID | Type | Source File | Title | Rejected |
|----|-------------|------|-------------|-------|----------|
| REJ-20251205-001 | N/A | Error | SPINDLE_PID_TUNING_GUIDE_v5.3.md | Encoder watchdog comparator polarity fix | 2025-12-05 |

---

## Entries

### REJ-20251205-001 Encoder watchdog comparator polarity fix

| Field | Value |
|-------|-------|
| Original ID | N/A |
| Type | Error |
| Source File | SPINDLE_PID_TUNING_GUIDE_v5.3.md |
| Location | N/A (HAL code not in this file) |
| Originally Submitted By | External AI Agent (ChatGPT) |
| Originally Submitted | 2025-12-05 |
| Rejected By | Claude (claude-opus-4-5-20251101) |
| Rejected | 2025-12-05 |

**Original Description:** The agent claimed the encoder watchdog comparator logic is "currently inverted" and provided a "drop-in replacement" for the watchdog compare section. The claim was that `comp` outputs TRUE when `in1 > in0` and the current "cmd > threshold?" and "fb < threshold?" checks are "wired the opposite way, so the watchdog likely never trips when it should."

**Original Rationale:** The agent referenced the LinuxCNC comp man page noting that comp outputs TRUE when `in1 > in0` (in0 is the inverting input). The agent provided complete HAL code replacement including signal renaming.

**Rejection Reason:** The comment is **out of scope** for this source file. The source file being evaluated (`SPINDLE_PID_TUNING_GUIDE_v5.3.md`) is a documentation/tuning guide that does **not contain** the encoder watchdog HAL implementation code. The guide only references signal names (e.g., `encoder-watchdog-is-armed`, `encoder-fault`) and expected values during verification tests.

The actual encoder watchdog HAL wiring would be located in a `.hal` file (such as `Grizzly7x14_Lathe.hal`), which is not part of this documentation file. The guide correctly describes what the watchdog should do and how to test it, but does not prescribe the specific comp/and/not wiring implementation.

If there is indeed a bug in the HAL implementation, it should be reported and evaluated against the actual `.hal` file containing the watchdog code, not this documentation guide.

**Rejection Category:**
- [ ] Not an error / Not beneficial
- [x] Out of scope
- [ ] Intentional design decision
- [ ] Would break existing functionality
- [ ] Duplicate of previous rejection
- [ ] Insufficient justification
- [ ] Misunderstanding of source material
- [ ] Other: [specify]

**Guidance for Future Agents:** When submitting comments about HAL code implementation, ensure the source file being evaluated actually contains that HAL code. Documentation guides that reference signal names are not the same as HAL files that define the signal wiring. Comments about HAL implementation bugs should be directed at the actual `.hal` files.

If this potential bug needs investigation, a separate evaluation should be conducted against the system's HAL configuration files (e.g., `Grizzly7x14_Lathe.hal` or `custom.hal`).

**Review History:**
- 2025-12-05 | External AI Agent | Submitted as critical logic fix for encoder watchdog comparator polarity.
- 2025-12-05 | Claude | Rejected: Out of scope - comment addresses HAL code not present in this documentation file.

---
