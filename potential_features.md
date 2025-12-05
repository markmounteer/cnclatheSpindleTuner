# Potential Features Register
**Directory:** /home/user/cnclatheSpindleTuner/
**Last Updated:** 2025-12-05 20:31 UTC
**Total Entries:** 16 | **New:** 16 | **Under Review:** 0 | **Resolved:** 0

## Summary Index
| ID | Status | Priority | Source File | Title | Submitted |
|----|--------|----------|-------------|-------|-----------|
| FEAT-20251205-001 | 🆕 New | 🟢 Low | dashboard.py | Error History Export | 2025-12-05 |
| FEAT-20251205-005 | 🆕 New | 🟢 Low | dashboard.py | Keyboard Shortcut Help Overlay | 2025-12-05 |
| FEAT-20251205-007 | 🆕 New | 🟢 Low | hal_interface.py | Add `__all__` Export List | 2025-12-05 |
| FEAT-20251205-009 | 🆕 New | 🟡 Medium | config.py | Split into Config Package | 2025-12-05 |
| FEAT-20251205-010 | 🆕 New | 🟡 Medium | config.py | Replace TypedDicts with Dataclasses | 2025-12-05 |
| FEAT-20251205-011 | 🆕 New | 🟢 Low | config.py | Use Enums for Categorical Values | 2025-12-05 |
| FEAT-20251205-012 | 🆕 New | 🟢 Low | config.py | Eliminate Duplicate Pin Mapping with Constant | 2025-12-05 |
| FEAT-20251205-013 | 🆕 New | 🟢 Low | config.py | Add Validation at Module Load | 2025-12-05 |
| FEAT-20251205-014 | 🆕 New | 🟢 Low | config.py | Use MappingProxyType for Immutability | 2025-12-05 |
| FEAT-20251205-015 | 🆕 New | 🟢 Low | config.py | Group Constants into Namespace Classes | 2025-12-05 |
| FEAT-20251205-016 | 🆕 New | 🟡 Medium | config.py | Structured Troubleshooting Data with Dataclasses | 2025-12-05 |
| FEAT-20251205-009 | 🆕 New | 🟡 Medium | hal_interface.py | Split Module Into Smaller Components | 2025-12-05 |
| FEAT-20251205-010 | 🆕 New | 🟡 Medium | hal_interface.py | Introduce Backend Interface for Mock/Real Abstraction | 2025-12-05 |
| FEAT-20251205-011 | 🆕 New | 🟢 Low | hal_interface.py | Decouple MockPhysicsEngine from MONITOR_PINS | 2025-12-05 |
| FEAT-20251205-012 | 🆕 New | 🟡 Medium | hal_interface.py | Replace TUNING_PARAMS Tuple Indexing with Dataclass Schema | 2025-12-05 |
| FEAT-20251205-013 | 🆕 New | 🟢 Low | hal_interface.py | Make Feature Probing Lazy (Avoid Import-Time Side Effects) | 2025-12-05 |
| FEAT-20251205-014 | 🆕 New | 🟢 Low | hal_interface.py | Centralize Subprocess Execution into HalcmdRunner Class | 2025-12-05 |
| FEAT-20251205-015 | 🆕 New | 🟢 Low | hal_interface.py | Narrow Lock Scope for Higher Concurrency | 2025-12-05 |
| FEAT-20251205-016 | 🆕 New | 🟡 Medium | hal_interface.py | Formalize Connection Health and Auto-Reconnect Policy | 2025-12-05 |
| FEAT-20251205-017 | 🆕 New | 🟢 Low | hal_interface.py | Introduce Data Models for Returned Telemetry | 2025-12-05 |
| FEAT-20251205-018 | 🆕 New | 🟢 Low | hal_interface.py | Split INI Handler Responsibilities and Add Atomic Writes | 2025-12-05 |
| FEAT-20251205-019 | 🆕 New | 🟢 Low | hal_interface.py | Make Configuration Injectable for Testing | 2025-12-05 |
| FEAT-20251205-020 | 🆕 New | 🟢 Low | config.py | Add Default Field to TuningParamSpec | 2025-12-05 |
| FEAT-20251205-021 | 🆕 New | 🟢 Low | config.py | Add Literal Type Aliases for Config Keys | 2025-12-05 |

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


### FEAT-20251205-009 Split into Config Package
### FEAT-20251205-009 Split Module Into Smaller Components

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Module-level |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | Entire module |
| Submitted By | Architecture Review Agent |
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
**Description:** Split the monolithic `hal_interface.py` into smaller, focused modules organized by responsibility.

**Context:** The current file (~1700 lines) combines platform probing, halcmd subprocess I/O, caching, mock physics, MDI handling, and INI file operations in a single module.

**Original Agent Rationale:** Reducing "scroll fatigue" makes it obvious where to add future features and improves code ownership clarity.

**Evaluator Assessment:** This is a valid architectural improvement suggestion. The module does combine multiple responsibilities that could be logically separated. However, the current implementation is functional and well-organized with clear section markers.

**Proposed Structure:**
```
spindle_tuner/
  hal/
    interface.py        # HalInterface facade + public API
    halcmd_backend.py   # halcmd get/set/bulk + parsing + pin validation
    linuxcnc_mdi.py     # send_mdi + linuxcnc state handling (optional)
    cache.py            # TTL cache utilities
    types.py            # enums/dataclasses (ConnectionState, CachedValue, etc.)
  mock/
    physics.py          # MockPhysicsEngine
    state.py            # MockState, PhysicsParameters
  ini/
    handler.py          # IniFileHandler + backup/atomic writes
    mapping.py          # INI<->param mapping/schema
```

**Implementation Considerations:**
- Would require updating all import statements across the codebase
- Increases file count and navigation complexity
- Need to maintain backward compatibility for existing consumers
- Risk of circular imports between split modules

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-010 Replace TypedDicts with Dataclasses
### FEAT-20251205-010 Introduce Backend Interface for Mock/Real Abstraction

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 145-195 (Hardware Specifications) |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | HalInterface class methods |
| Submitted By | Architecture Review Agent |
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
**Description:** Define a protocol/ABC that both real and mock backends implement to eliminate scattered `if self.is_mock:` branches.

**Context:** Multiple methods in HalInterface contain conditional logic to handle mock vs. real HAL operations (e.g., `get_pin_value`, `set_param`, `send_mdi`, `validate_pin`).

**Original Agent Rationale:** HalInterface would become an orchestration layer (caching, stats, reconnection policy) without needing conditional mock checks in every method.

**Evaluator Assessment:** This is a sound design pattern that would improve code maintainability. The current approach works but spreads mock-handling logic throughout the class.

**Proposed Interface:**
```python
class HalBackend(Protocol):
    def read(self, pin: str) -> float: ...
    def read_many(self, pins: list[str]) -> dict[str, float]: ...
    def write(self, pin: str, value: float) -> bool: ...
    def validate(self, pin: str) -> bool: ...
```

**Implementation Considerations:**
- Requires refactoring ~10 methods
- May add indirection that complicates debugging
- Need to handle edge cases where mock and real behavior differ intentionally
- Performance impact of additional abstraction layer

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-011 Use Enums for Categorical Values
### FEAT-20251205-011 Decouple MockPhysicsEngine from MONITOR_PINS

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 202-293, 126-138 |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | MockPhysicsEngine.update() method (lines 199-405) |
| Submitted By | Architecture Review Agent |
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
**Description:** Have MockPhysicsEngine return semantic keys instead of HAL pin names, with mapping done by the mock backend layer.

**Context:** `MockPhysicsEngine.update()` builds output using `MONITOR_PINS` and returns pin-name → value pairs, tying the simulator to the current HAL naming scheme.

**Original Agent Rationale:** Returning semantic keys makes the physics engine reusable in tests and non-HAL UIs without dependency on specific pin naming conventions.

**Evaluator Assessment:** This is a reasonable decoupling suggestion that would improve testability. The physics engine's core simulation logic is independent of HAL naming.

**Proposed Change:**
```python
# Instead of returning {"spindle.0.actual-rpm": 1500.0}
# Return {"cmd_raw": ..., "feedback": ..., "at_speed": ...}
# Let the mock backend map to pin names via MONITOR_PINS
```

**Implementation Considerations:**
- Requires adding a mapping layer between physics engine and mock backend
- May slightly increase complexity for a relatively minor benefit
- Need to ensure all semantic keys are well-documented
- Backward compatibility for any code that accesses mock_values directly

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-012 Eliminate Duplicate Pin Mapping with Constant
### FEAT-20251205-012 Replace TUNING_PARAMS Tuple Indexing with Dataclass Schema

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
| Source File | hal_interface.py |
| Location | Multiple locations referencing TUNING_PARAMS |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

**Description:** Replace `TUNING_PARAMS` tuple/list indexing (e.g., `meta[0]`, `meta[2]`, `meta[4]`) with a typed dataclass schema.

**Context:** The code uses defensive length checks like `if len(meta) > 2` when accessing tuple indices, which is error-prone and not self-documenting.

**Original Agent Rationale:** A dataclass provides a single source of truth for bounds/step snapping, pin name, and INI key mapping, making the code more maintainable.

**Evaluator Assessment:** This is a valid improvement. The current tuple-based approach requires developers to remember index meanings and is prone to off-by-one errors.

**Proposed Schema:**
```python
@dataclass(frozen=True)
class ParamMeta:
    pin: str
    min: float = -inf
    max: float = inf
    step: float = 0.0
    ini_key: str | None = None
```

**Implementation Considerations:**
- Requires updating `config.py` where TUNING_PARAMS is defined
- Need to update all consumers across the codebase
- May require migration logic if config is persisted
- Would improve IDE autocomplete and type checking

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-013 Add Validation at Module Load
### FEAT-20251205-013 Make Feature Probing Lazy (Avoid Import-Time Side Effects)

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | After PRESETS definition (line 138) |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | Lines 60-83 (module-level platform detection) |
| Submitted By | Architecture Review Agent |
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
**Description:** Move platform probing (`HAS_HALCMD`, `HAS_LINUXCNC`) into helper functions called during `HalInterface.__init__()` rather than at import time.

**Context:** Currently, `HAS_HALCMD` and platform logging happen at module import time, which can cause issues in tests and when the module is imported as a library.

**Original Agent Rationale:** Keeping module import "quiet" unless instantiated improves testability and avoids unexpected side effects when importing.

**Evaluator Assessment:** This is a minor but valid improvement. The current import-time detection logs messages and runs `shutil.which()` which isn't ideal for library usage.

**Proposed Functions:**
```python
def detect_halcmd() -> bool: ...
def detect_linuxcnc_module() -> bool: ...
# Called in HalInterface.__init__() instead of module scope
```

**Implementation Considerations:**
- Minor refactoring with low risk
- Need to handle cases where detection is checked before instantiation
- May want to cache detection results to avoid repeated checks
- Could use `functools.cache` for lazy singleton behavior

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-014 Use MappingProxyType for Immutability
### FEAT-20251205-014 Centralize Subprocess Execution into HalcmdRunner Class

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 112-138 (BASELINE_PARAMS, PRESETS) |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | _run_halcmd() and subprocess.run() calls |
| Submitted By | Architecture Review Agent |
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
**Description:** Consolidate all halcmd subprocess execution into a dedicated `HalcmdRunner` class with consistent error handling and timeout policies.

**Context:** The module has `_run_halcmd()` plus additional `subprocess.run()` usage in bulk read/write methods with slightly different handling.

**Original Agent Rationale:** A single component provides consistent timeout policy, stderr/returncode handling, optional tracing/metrics, and a single place for future optimizations (like a persistent Popen session).

**Evaluator Assessment:** This would improve consistency and make it easier to add features like retry logic or metrics. The current approach works but has some duplication.

**Proposed Features:**
- Consistent timeout policy
- Typed exceptions (`HalcmdTimeout`, `HalcmdCommandError`, `HalValueParseError`)
- Optional tracing/metrics
- Future optimization: persistent Popen session

**Implementation Considerations:**
- Moderate refactoring effort
- Need to preserve existing behavior while consolidating
- Typed exceptions would improve error handling in callers
- Consider if a class or module-level functions are more appropriate

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-015 Group Constants into Namespace Classes
### FEAT-20251205-015 Narrow Lock Scope for Higher Concurrency

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 331-343 (PLOT_TRACES, PLOT_DEFAULTS) |
| Submitted By | Config Review Agent |
| Source File | hal_interface.py |
| Location | Methods holding self._lock during subprocess calls |
| Submitted By | Architecture Review Agent |
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
**Description:** Reduce lock scope by acquiring `self._lock` only for cache/state operations, not during slow subprocess calls.

**Context:** Many methods hold `self._lock` while doing `subprocess.run(...)`, blocking all readers while the process runs.

**Original Agent Rationale:** Narrowing lock scope to only check/update cache, update state fields, and update `_pin_access_mode` would allow higher concurrency.

**Evaluator Assessment:** This is a valid optimization for concurrent access. However, the current implementation prioritizes thread safety over concurrency, which is appropriate for a single-user GUI application.

**Proposed Pattern:**
```python
# Acquire lock only to check/update cache
# Release during slow subprocess call
# Reacquire to store results
```

**Implementation Considerations:**
- Increases complexity and risk of race conditions
- Need careful analysis of what state can change during subprocess execution
- May not provide significant benefit for typical single-threaded GUI usage
- Could introduce subtle bugs if not implemented carefully

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-016 Structured Troubleshooting Data with Dataclasses
### FEAT-20251205-016 Formalize Connection Health and Auto-Reconnect Policy

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
| Source File | hal_interface.py |
| Location | Connection management section |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | Related to FEAT-20251205-008 |

**Description:** Introduce dedicated `HealthMonitor` and `ConnectionPolicy` classes to formalize connection health tracking and auto-reconnect behavior.

**Context:** Connection happens once at init, and after that the read path doesn't update connection state on repeated failures.

**Original Agent Rationale:** Extracting the "state machine" logic from low-level read methods into dedicated classes would improve maintainability and enable more sophisticated reconnection strategies.

**Evaluator Assessment:** This overlaps with FEAT-20251205-008 (HAL reconnection attempts) but proposes a more comprehensive architectural solution. Both address the same underlying concern about connection reliability.

**Proposed Components:**
- `HealthMonitor`: tracks consecutive failures, last success, last error
- `ConnectionPolicy`: determines when to mark ERROR, when to retry, when to switch to mock fallback

**Implementation Considerations:**
- More comprehensive than simple retry logic
- Adds architectural complexity
- May be overkill for typical single-machine usage
- Consider combining with FEAT-20251205-008 for unified approach

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; noted relation to FEAT-20251205-008; added to register.

---

### FEAT-20251205-017 Introduce Data Models for Returned Telemetry

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | get_all_values() method |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Return a typed `Telemetry` dataclass from a new `get_telemetry()` method instead of an untyped dictionary.

**Context:** `get_all_values()` returns a dict keyed by logical names, which becomes hard to discover fields and type-check as it grows.

**Original Agent Rationale:** A dataclass provides IDE autocomplete, type checking, and clear documentation of available fields.

**Evaluator Assessment:** This would improve developer experience and type safety. The current dict approach is flexible but lacks discoverability.

**Proposed Model:**
```python
@dataclass
class Telemetry:
    cmd_raw: float
    feedback: float
    at_speed: bool
    # ... other fields

# Usage: telemetry = hal.get_telemetry()
# Keep get_all_values() for backward compatibility
```

**Implementation Considerations:**
- Need to maintain backward compatibility with get_all_values()
- Dataclass fields must stay synchronized with MONITOR_PINS
- Consider making some fields Optional for pins that may not exist
- May want to add computed properties for derived values

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-018 Split INI Handler Responsibilities and Add Atomic Writes

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | IniFileHandler class (lines 1447-1718) |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Split `IniFileHandler` into `IniReader`, `IniWriter`, and `BackupManager` components, and implement atomic write operations.

**Context:** `IniFileHandler` currently combines reading, mapping, backing up, and generating text. The module also lacks atomic write support if "write back to INI" is added.

**Original Agent Rationale:** Separation of concerns improves maintainability; atomic writes prevent corrupted INIs on crashes.

**Evaluator Assessment:** Splitting the class may be overkill given its current size (~270 lines), but atomic writes would be a valuable safety feature.

**Proposed Components:**
- `IniReader`: read_section, read_spindle_params
- `IniWriter`: generate section, write/merge
- `BackupManager`: list/create backups

**Atomic Write Pattern:**
```python
# Write to temp file in same directory
# fsync()
# rename() over original
```

**Implementation Considerations:**
- Current class is relatively small and cohesive
- Atomic writes would be valuable if write functionality is added
- Splitting might increase complexity without proportional benefit
- Consider implementing only atomic writes without full split

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-019 Make Configuration Injectable for Testing

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Module imports and class constructors |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Accept configuration as constructor parameters instead of importing global constants from `config.py`.

**Context:** The module imports `MONITOR_PINS`, `TUNING_PARAMS`, etc. from config at module level, making it difficult to test with different configurations.

**Original Agent Rationale:** Dependency injection enables unit testing and reuse with different configurations. Defaults can still come from `config.py`, but callers can override cleanly.

**Evaluator Assessment:** This is a standard testability improvement. The current approach tightly couples the module to config.py.

**Proposed Pattern:**
```python
@dataclass
class Config:
    monitor_pins: dict[str, str]
    tuning_params: dict[str, ParamMeta]
    baseline_params: dict[str, float]
    # ...

# Usage:
HalInterface(config: Config = default_config)
IniFileHandler(config: Config = default_config)
MockPhysicsEngine(config: Config = default_config)
```

**Implementation Considerations:**
- Moderate refactoring effort
- Need to define what belongs in injectable Config vs. stays global
- Default values preserve current behavior for normal usage
- Significantly improves unit test isolation

**Review History:**
- 2025-12-05 | Architecture Review Agent | Submitted comment.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-020 Add Default Field to TuningParamSpec

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | Lines 80-105 (TuningParamSpec and TUNING_PARAMS) |
| Submitted By | Config Architecture Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Add a `default` field to `TuningParamSpec` NamedTuple and automatically derive `BASELINE_PARAMS` from `TUNING_PARAMS`, eliminating the need to maintain two parallel data structures.

**Context:** Currently, baseline values are defined separately in `BASELINE_PARAMS` (lines 112-123) while parameter metadata is defined in `TUNING_PARAMS` (lines 94-105). This separation requires keeping both in sync manually.

**Original Agent Rationale:** The submitting agent argued this "eliminates drift when someone updates one but forgets the other" by making `BASELINE_PARAMS` derived automatically:
```python
# Add default to TuningParamSpec
class TuningParamSpec(NamedTuple):
    hal_pin: str
    description: str
    min_val: float
    max_val: float
    step: float
    ini_section: str
    ini_key: str
    default: float  # NEW

# Derive baseline automatically
BASELINE_PARAMS = {k: spec.default for k, spec in TUNING_PARAMS.items()}
```

**Evaluator Assessment:** This is a valid DRY (Don't Repeat Yourself) principle application. However, the current separation has benefits: explicit `BASELINE_PARAMS` is easier to read and modify without navigating through `TuningParamSpec` definitions. The test suite (`test_config.py`) should catch sync issues.

**Implementation Considerations:**
- Requires updating `TuningParamSpec` NamedTuple (adds 10th field)
- Would need to update all `TuningParamSpec(...)` calls in TUNING_PARAMS
- Type hints remain compatible (adds `default: float` field)
- Backward compatibility: existing code accessing tuple indices would need updating
- Risk: Makes `TUNING_PARAMS` definitions longer and harder to scan visually

**Review History:**
- 2025-12-05 | Config Architecture Agent | Submitted as DRY improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; added to register.

---

### FEAT-20251205-021 Add Literal Type Aliases for Config Keys

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | config.py |
| Location | After imports (line 16) |
| Submitted By | Config Architecture Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

**Description:** Define `Literal` type aliases for commonly-used string keys to catch typos at static analysis time while preserving the current string-based API.

**Context:** Multiple string literals are repeated throughout the codebase (e.g., `"SPINDLE_0"`, `"P"`, `"I"`, `"baseline"`, `"cmd_raw"`). Typos in these strings cause silent failures.

**Original Agent Rationale:** The submitting agent proposed:
```python
from typing import Literal

MonitorKey = Literal["cmd_raw", "cmd_limited", "feedback", "feedback_raw", ...]
ParamName = Literal["P", "I", "D", "FF0", "FF1", "Deadband", ...]
PresetName = Literal["baseline", "conservative", "aggressive"]

# Usage in function signatures:
def get_preset(name: PresetName) -> Preset: ...
def get_monitor_pin(name: MonitorKey, default: Optional[str] = None) -> str: ...
```

**Evaluator Assessment:** This differs from FEAT-20251205-011 (Enums) in that Literal types don't change runtime behavior - they only add type hints. Type checkers like mypy would catch invalid string literals at analysis time. This is a low-risk enhancement that improves developer experience.

**Implementation Considerations:**
- Non-breaking change: runtime behavior unchanged
- Requires Python 3.8+ (already satisfied)
- Adds ~15 lines of type alias definitions
- Benefits are visible only when using mypy or similar tools
- Must keep Literal types synchronized with actual dict keys
- Alternative: Use `typing.get_args()` to validate at test time

**Review History:**
- 2025-12-05 | Config Architecture Agent | Submitted as type safety improvement.
- 2025-12-05 | Claude Opus 4 | Evaluated as feature suggestion; distinct from Enum approach in FEAT-20251205-011; added to register.

---
