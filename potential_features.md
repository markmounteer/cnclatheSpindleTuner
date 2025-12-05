# Potential Features Register
**Directory:** /home/user/cnclatheSpindleTuner/
**Last Updated:** 2025-12-05 20:30 UTC
**Total Entries:** 16 | **New:** 16 | **Under Review:** 0 | **Resolved:** 0

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
| FEAT-20251205-009 | 🆕 New | 🟡 Medium | config.py | Split into Config Package | 2025-12-05 |
| FEAT-20251205-010 | 🆕 New | 🟡 Medium | config.py | Replace TypedDicts with Dataclasses | 2025-12-05 |
| FEAT-20251205-011 | 🆕 New | 🟢 Low | config.py | Use Enums for Categorical Values | 2025-12-05 |
| FEAT-20251205-012 | 🆕 New | 🟢 Low | config.py | Eliminate Duplicate Pin Mapping with Constant | 2025-12-05 |
| FEAT-20251205-013 | 🆕 New | 🟢 Low | config.py | Add Validation at Module Load | 2025-12-05 |
| FEAT-20251205-014 | 🆕 New | 🟢 Low | config.py | Use MappingProxyType for Immutability | 2025-12-05 |
| FEAT-20251205-015 | 🆕 New | 🟢 Low | config.py | Group Constants into Namespace Classes | 2025-12-05 |
| FEAT-20251205-016 | 🆕 New | 🟡 Medium | config.py | Structured Troubleshooting Data with Dataclasses | 2025-12-05 |

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

### FEAT-20251205-009 Split into Config Package

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Module-level |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** Refactor the single config.py file into a config package with multiple modules organized by concern.

**Context:** The current config.py handles multiple concerns: application constants, HAL pins, hardware specs, presets, troubleshooting data, and plot configuration all in one 405-line file.

**Original Agent Rationale:** The submitting agent argued that the file "handles too many concerns" and proposed a structure with separate modules: `app.py`, `hal_pins.py`, `hardware.py`, `presets.py`, `troubleshooting.py`, and `plot.py`.

**Evaluator Assessment:** While separation of concerns is a valid software engineering principle, the current monolithic config file has benefits: single import location, easy grep-ability, no circular import risks, and clear section headers already organize the content logically. The 405-line file size is manageable.

**Implementation Considerations:**
- Would require updating all imports across the codebase
- Risk of circular imports between config modules
- Adds complexity for users who want to view all configuration at once
- Would need a proper `__init__.py` to re-export public API
- Potential benefits increase if config grows significantly larger

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as architectural improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-010 Replace TypedDicts with Dataclasses

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 145-195 (Hardware Specifications) |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** Convert `MotorSpecs`, `VfdSpecs`, and `EncoderSpecs` TypedDicts to frozen dataclasses for immutability and better ergonomics.

**Context:** The current code uses TypedDict for hardware specification types with corresponding dictionary instances:
```python
class MotorSpecs(TypedDict):
    name: str
    power_hp: float
    ...

MOTOR_SPECS: MotorSpecs = {
    "name": "Baldor M3558T",
    ...
}
```

**Original Agent Rationale:** The submitting agent argued that dataclasses provide immutability via `frozen=True`, allow adding computed properties (e.g., `slip_range`), and offer "better ergonomics" than TypedDicts.

**Evaluator Assessment:** TypedDicts are appropriate here because they type-check dictionary literals, which is the format used throughout the codebase. Dataclasses would change access patterns from `MOTOR_SPECS["name"]` to `MOTOR_SPECS.name`, requiring updates to all consumers. The frozen dataclass immutability is not strictly necessary since dictionaries can be protected via `.copy()` patterns already in use.

**Implementation Considerations:**
- Would change all access patterns throughout codebase
- Dataclass attribute access (`MOTOR_SPECS.name`) vs dict access (`MOTOR_SPECS["name"]`)
- Would lose TypedDict compatibility with JSON serialization patterns
- Computed properties could be added as standalone functions instead
- May break external consumers expecting dict-like objects

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as design pattern improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-011 Use Enums for Categorical Values

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 202-293, 126-138 |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Replace string literals for severity colors and preset names with Enum types for type safety.

**Context:** The current code uses string literals for severity colors in `SYMPTOM_DIAGNOSIS` (e.g., `"orange"`, `"yellow"`, `"red"`) and preset names in `PRESETS` (e.g., `"conservative"`, `"baseline"`, `"aggressive"`).

**Original Agent Rationale:** The submitting agent proposed `Severity` and `PresetName` enums to provide type safety and prevent typos in string values.

**Evaluator Assessment:** While enums would add type safety, the current string values are used in limited, well-tested contexts. Severity strings map directly to Tkinter color names, and preset names are validated by `get_preset()` which raises `KeyError` for invalid names. The simplicity of string comparison outweighs enum benefits for this use case.

**Implementation Considerations:**
- Severity strings are used directly as Tkinter colors; enum would need `.value` access
- Preset names would require enum-to-string conversion for UI display
- Limited benefit given small, fixed sets of values
- Type checkers already catch invalid dict keys at static analysis time
- Would add import dependencies for Enum

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as type safety improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-012 Eliminate Duplicate Pin Mapping with Constant

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 74-77 |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Extract the duplicate `"external-ok"` HAL pin value into a private constant to eliminate duplication.

**Context:** The current code has:
```python
# Safety chain / external OK (tests use external_ok; main/dashboard use safety_chain)
"external_ok":   "external-ok",
"safety_chain":  "external-ok",
```

**Original Agent Rationale:** The submitting agent called this a "maintenance hazard" and proposed:
```python
_EXTERNAL_OK_PIN = "external-ok"
MONITOR_PINS: Dict[str, str] = {
    "external_ok": _EXTERNAL_OK_PIN,
    "safety_chain": _EXTERNAL_OK_PIN,
}
```

**Evaluator Assessment:** The existing comment clearly documents the intentional duplication and explains why both keys exist. The duplication is a deliberate design choice to support different naming conventions in different modules. A constant adds indirection without meaningful benefit since the HAL pin name (`"external-ok"`) is unlikely to change, and if it did, a simple find-replace would suffice.

**Implementation Considerations:**
- Minimal maintenance benefit; the value is unlikely to change
- Adds indirection that reduces readability
- Comment already explains the design decision
- Could confuse readers who wonder why a constant is used for one pin but not others
- Alternative: single canonical name with documentation for alias usage

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as maintainability improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-013 Add Validation at Module Load

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | After PRESETS definition (line 138) |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add a validation function that runs at module import time to ensure `BASELINE_PARAMS` and `PRESETS` keys stay synchronized with `TUNING_PARAMS`.

**Context:** The submitting agent proposed:
```python
def _validate_config():
    tuning_keys = set(TUNING_PARAMS.keys())
    baseline_keys = set(BASELINE_PARAMS.keys())
    if tuning_keys != baseline_keys:
        missing = tuning_keys - baseline_keys
        extra = baseline_keys - tuning_keys
        raise ValueError(f"BASELINE_PARAMS mismatch. Missing: {missing}, Extra: {extra}")

_validate_config()
```

**Original Agent Rationale:** Ensures consistency between related configuration dictionaries and fails fast if they diverge.

**Evaluator Assessment:** This is a reasonable defensive programming technique. However, the test suite (`test_config.py`) should already catch such mismatches. Adding runtime validation in production code increases import time and fails the entire application rather than just tests. The appropriate place for this validation is in the test suite.

**Implementation Considerations:**
- Increases module import time (runs on every import)
- Fails entire application rather than just tests
- Better suited for test suite validation
- Could be useful during development with a debug flag
- Would need to also validate each preset's keys against TUNING_PARAMS

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as defensive programming improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-014 Use MappingProxyType for Immutability

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 112-138 (BASELINE_PARAMS, PRESETS) |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Wrap configuration dictionaries in `MappingProxyType` to make them truly immutable at runtime.

**Context:** The submitting agent noted that helper functions return `.copy()` to prevent mutation but proposed making the originals immutable:
```python
from types import MappingProxyType

BASELINE_PARAMS: Mapping[str, float] = MappingProxyType({
    "P": 0.1,
    ...
})
```

**Original Agent Rationale:** Prevents accidental mutation of the original dictionaries, providing stronger guarantees than the current `.copy()` pattern.

**Evaluator Assessment:** The existing `get_baseline_params()` and `get_preset()` functions already return copies, protecting the originals. `MappingProxyType` adds complexity and changes the type signature from `Dict` to `Mapping`, potentially breaking type hints in consuming code. The risk of accidental mutation is low given the explicit helper functions.

**Implementation Considerations:**
- Changes type from `Dict` to `Mapping`, affecting type hints
- `MappingProxyType` objects don't support `.copy()` directly
- Would require updating type annotations throughout codebase
- Adds import dependency from `types` module
- May confuse developers unfamiliar with `MappingProxyType`
- Current `.copy()` pattern is idiomatic Python

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as immutability improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-015 Group Constants into Namespace Classes

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 331-343 (PLOT_TRACES, PLOT_DEFAULTS) |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Group related constants into namespace classes for better organization.

**Context:** The submitting agent proposed:
```python
class Plot:
    TRACES: Final = MappingProxyType({...})
    DEFAULTS: Final = MappingProxyType({...})

# Usage: Plot.TRACES["cmd"]["color"]
```

**Original Agent Rationale:** Provides logical grouping and namespace organization for related constants.

**Evaluator Assessment:** While namespace classes can improve organization, they add an extra level of indirection. The current `PLOT_TRACES` and `PLOT_DEFAULTS` naming with section comments is clear and conventional for Python configuration modules. Namespace classes are more common in languages without module-level namespacing.

**Implementation Considerations:**
- Adds indirection: `Plot.TRACES` vs `PLOT_TRACES`
- Would require updating all import statements and usages
- Python modules already provide namespacing via `import config`
- Class-based namespacing is not idiomatic Python for configuration
- May complicate IDE autocomplete behavior
- Benefit is primarily aesthetic

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as organizational improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-016 Structured Troubleshooting Data with Dataclasses

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 202-293 (SYMPTOM_DIAGNOSIS) |
| Submitted By | Config Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** Replace the tuple-based `SYMPTOM_DIAGNOSIS` structure with frozen dataclasses for better queryability and type safety.

**Context:** The current code uses:
```python
SYMPTOM_DIAGNOSIS: List[Tuple[str, str, str]] = [
    (
        "Fast Oscillation (>1 Hz)",
        "- Reduce P-gain (try 0.05)\n...",
        "orange",
    ),
    ...
]
```

The submitting agent proposed:
```python
@dataclass(frozen=True)
class SymptomDiagnosis:
    symptom: str
    remedies: list[str]  # List instead of multiline string
    severity: Severity

SYMPTOM_DIAGNOSES: tuple[SymptomDiagnosis, ...] = (...)
```

**Original Agent Rationale:** Makes the data queryable (e.g., filter by severity), avoids parsing embedded newlines, and provides better type safety.

**Evaluator Assessment:** This is a reasonable structural improvement. The current tuple structure with multiline strings is harder to process programmatically. However, the data is currently used only for display in the troubleshooter UI, where the multiline format maps directly to how it's rendered. Converting to list[str] would require changes to the rendering code.

**Implementation Considerations:**
- Would require updating troubleshooter.py rendering code
- Benefit of queryability only matters if filtering/searching is needed
- Current format directly matches UI display requirements
- Dataclass would add import overhead
- Could break any code parsing the tuple structure
- Would benefit future features like symptom search or filtering

**Review History:**
- 2025-12-05 | Config Review Agent | Submitted as data structure improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---
