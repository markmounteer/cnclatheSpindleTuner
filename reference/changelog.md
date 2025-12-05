# Changelog — reference/

This changelog documents implemented features for files in the `/reference/` directory.

---

## 2025-12-06 — Feature Implementation

**Implemented:** FEAT-20251205-002 — Add DPLL phase-error diagnostic net

**Source File:** /home/user/cnclatheSpindleTuner/reference/SPINDLE_PID_TUNING_GUIDE_v5.3.md

**Description:**
Added documentation for creating a named HAL signal for DPLL phase-error monitoring in HALShow. This provides an alternative to the existing `watch` command approach, making it easier to monitor phase error through the HALShow graphical interface.

**Changes Made:**
- Added 2 lines to Section 5.4 (DPLL Verification) after the existing `watch` command
- Added comment: `# Optional: Create a named signal for easier HALShow monitoring`
- Added HAL command: `net hm2-dpll-phase-error hm2_7i76e.0.dpll.phase-error-us`

**Original Request:**
- Submitted By: External AI Agent (ChatGPT)
- Submitted: 2025-12-05
- Priority: Low
- Register: /home/user/cnclatheSpindleTuner/reference/potential_features.md

**Implementation:**
- Implemented By: Claude (claude-opus-4-5-20251101)
- Implemented: 2025-12-06

**Selection Rationale:**
This feature was selected from 31 eligible features across 4 registers based on the weighted scoring system. It tied for highest score (2.2) with 6 other features and was selected via alphabetical tiebreaker on Feature ID. The feature has minimal implementation effort (documentation-only change), no dependencies, and clear scope.

**Evaluation Score:**
- Impact: 1/4 (Low - minor convenience enhancement)
- Effort: 3/3 (Minimal - single line addition)
- Dependencies: 3/3 (None - self-contained)
- Clarity: 3/3 (Clear - well-defined scope)
- Total: 2.2

**Competing Features:**
- FEAT-20251205-003 (reference) — Score: 2.2 — Document lowpass filter gain formula
- FEAT-20251205-004 (dashboard.py) — Score: 2.2 — Fallback Chart Error Trace Scaling Indicator
- FEAT-20251205-006 (reference) — Score: 2.2 — Add at-speed relative tolerance with scale
- FEAT-20251205-007 (hal_interface.py) — Score: 2.2 — Add `__all__` Export List
- FEAT-20251205-013 (hal_interface.py) — Score: 2.2 — Make Feature Probing Lazy
- FEAT-20251205-021 (config.py) — Score: 2.2 — Add Literal Type Aliases for Config Keys

---

## 2025-12-05 — Feature Implementation

**Implemented:** FEAT-20251205-005 — Spindle safety hardening with E-stop gate

**Source File:** /home/user/cnclatheSpindleTuner/reference/SPINDLE_PID_TUNING_GUIDE_v5.3.md

**Description:**
Added safety hardening recommendations to Section 13 (Commissioning Cleanup) covering E-stop chain gating for spindle enable and optional speed filter reset on disable.

**Changes Made:**
- Added new Section 13.4 "Safety Hardening Recommendations"
- Documented HAL pattern for gating spindle-on with external-ok via and2 component
- Added optional speed filter reset recommendation using lowpass.load input
- Renumbered Section 13.4 "Documentation & Backup" to Section 13.5
- Updated document header Last Updated timestamp

**Original Request:**
- Submitted By: External AI Agent (ChatGPT)
- Submitted: 2025-12-05
- Priority: Medium
- Register: /home/user/cnclatheSpindleTuner/reference/potential_features.md

**Implementation:**
- Implemented By: Claude Opus 4 (claude-opus-4-5-20251101)
- Implemented: 2025-12-05

**Selection Rationale:**
This feature was selected as the highest-scoring item from 27 total features across 4 registers. It combined a Medium priority safety improvement with Minimal implementation effort (documentation-only change). The safety-related nature provided higher impact value while the documentation format ensured zero risk of breaking functionality.

**Evaluation Score:**
- Impact: 2/4 (Medium - safety improvement)
- Effort: 3/3 (Minimal - documentation update)
- Dependencies: 3/3 (None - self-contained)
- Clarity: 2/3 (Adequate)
- Total: 2.50

**Competing Features:**
- FEAT-20251205-008 (root) — Score: 2.20 — Implement Optional HAL Reconnection Attempts
- FEAT-20251205-007 (root) — Score: 2.20 — Add `__all__` Export List

---
