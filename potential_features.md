# Potential Features Register
**Directory:** /home/user/cnclatheSpindleTuner/
**Last Updated:** 2025-12-05 19:30 UTC
**Total Entries:** 19 | **New:** 19 | **Under Review:** 0 | **Resolved:** 0

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

### FEAT-20251205-009 Split Module Into Smaller Components

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Entire module |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

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

### FEAT-20251205-010 Introduce Backend Interface for Mock/Real Abstraction

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | HalInterface class methods |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟡 Medium |
| Duplicate Of | N/A |

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

### FEAT-20251205-011 Decouple MockPhysicsEngine from MONITOR_PINS

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | MockPhysicsEngine.update() method (lines 199-405) |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

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

### FEAT-20251205-012 Replace TUNING_PARAMS Tuple Indexing with Dataclass Schema

| Field | Value |
|-------|-------|
| Status | 🆕 New |
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

### FEAT-20251205-013 Make Feature Probing Lazy (Avoid Import-Time Side Effects)

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Lines 60-83 (module-level platform detection) |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

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

### FEAT-20251205-014 Centralize Subprocess Execution into HalcmdRunner Class

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | _run_halcmd() and subprocess.run() calls |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

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

### FEAT-20251205-015 Narrow Lock Scope for Higher Concurrency

| Field | Value |
|-------|-------|
| Status | 🆕 New |
| Source File | hal_interface.py |
| Location | Methods holding self._lock during subprocess calls |
| Submitted By | Architecture Review Agent |
| Evaluated By | Claude Opus 4 |
| Submitted | 2025-12-05 |
| Priority | 🟢 Low |
| Duplicate Of | N/A |

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

### FEAT-20251205-016 Formalize Connection Health and Auto-Reconnect Policy

| Field | Value |
|-------|-------|
| Status | 🆕 New |
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
