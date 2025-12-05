# Spindle Tuner v6.0 - tests_pytest Review (2025-12-05)

## Summary

Reviewed all files under `tests_pytest/` with the structured multi-pass process. No confirmed errors were found, so no source corrections were required. Initialized directory-specific registers for potential errors, features, and rejected changes with zero entries recorded.

---

## Corrections Applied

- None (files already consistent).

## Documentation Created

- `potential_errors.md`: Initialized register with no entries.
- `potential_features.md`: Initialized register with no entries.
- `rejected_changes.md`: Initialized register with no entries.

## Verification

- Not run (documentation-only updates).


# Spindle Tuner v6.0 - Tests Folder Review (2025-12-05)

## Summary

Reviewed all files under `tests/` following the structured multi-pass process. No uncertain errors or feature
suggestions were identified, and register files were initialized for future tracking. Applied one confirmed
correction and recompiled the test suite to verify syntax.

---

## Corrections Applied

### 1. Removed Unused Import in Forward PID Test

**Problem**: `statistics` was imported but never used in `tests/test_forward.py`, causing an avoidable lint issue.

**Fix**: Removed the unused import to keep the test module clean.

---

## Verification

- `python -m compileall tests`

# Spindle Tuner v6.0 - hal_interface.py Review (Grammar Updates)
# Spindle Tuner v6.0 - dashboard.py Review (2025-12-05)

## Summary

Reviewed `dashboard.py` for errors. Applied **2 confirmed corrections** and documented uncertain issues and feature suggestions for review.

---

## Corrections Applied

### 1. Formatting Inconsistency in Text Fallback (Line 921)

**Problem**: The "Integrator:" label in the text fallback display was missing the space after the colon, unlike all other labels which include spacing for alignment.

**Fix**:
```python
# Before
f"Integrator:{errI:8.1f}\n"

# After
f"Integrator: {errI:8.1f}\n"
```

### 2. Undefined Variable Bug in Fallback Chart (Line 937)

**Problem**: The `_update_text_fallback` method defined a local variable `err` but the code used `error` when appending to chart data. This would cause a `NameError` at runtime.

**Fix**:
```python
# Before
self.fallback_chart_data.append({
    ...
    'error': error,  # NameError: 'error' not defined
    ...
})

# After
self.fallback_chart_data.append({
    ...
    'error': err,  # Uses correct local variable
    ...
})
```

## Documentation Created

- `potential_errors.md`: 2 uncertain issues documented for verification
- `potential_features.md`: 5 enhancement suggestions documented for future consideration

## Verification

- Syntax check: `python3 -m py_compile dashboard.py` ✓
# Spindle Tuner v6.0 - hal_interface.py Review

## Date: 2025-12-05

## Summary

Applied minor grammar fixes to hal_interface.py and documented newly identified potential errors and feature ideas for further review.

## Corrections Applied

### 1. Grammar: Clarified Return and Usage Descriptions

- **File**: `hal_interface.py`
- **Issue**: Docstrings contained missing articles and a run-on sentence describing bulk reads.
- **Fix**: Added missing articles in return descriptions and introduced a comma to correct the sentence structure in the bulk read docstring.

## Documentation Updated

- **potential_errors.md**: Added an entry about the docstring claim of auto-reconnect behavior requiring verification.
- **potential_features.md**: Added a suggestion to implement optional reconnection attempts before falling back to mock mode.

## Files Modified

| File | Changes |
|------|---------|
| hal_interface.py | Grammar fixes in docstrings |
| potential_errors.md | Added new potential issue entry |
| potential_features.md | Added new feature suggestion |
| CHANGELOG.md | Updated with latest review details |

## Review Process

- Phase 1: First pass review - identified docstring grammar issues
- Phase 2: Second pass review - rechecked for additional errors
- Phase 3: Documented uncertain items in potential_errors.md
- Phase 4: Documented feature ideas in potential_features.md
- Phase 5: Applied confirmed grammar corrections only
- Phase 6: Updated changelog with summary and documentation notes

---
# Spindle Tuner v6.0 - hal_interface.py Review

# Spindle Tuner v6.0 - Code Quality Improvements

## Summary

Three pull requests merged to improve code quality, type safety, and maintainability across the codebase.

---

## PR #1: Improve config.py Structure and Type Safety

### Changes to config.py
- Add comprehensive type hints with `Final`, `NamedTuple`, `Dict`, `List`, `Tuple`
- Add `TuningParamSpec` NamedTuple for better parameter metadata
- Add `external_ok` alias in `MONITOR_PINS` for tests.py compatibility
- Maintain `safety_chain` for main.py/dashboard.py backward compatibility
- Add computed constants: `UPDATE_HZ`, `HISTORY_SAMPLES`, `GUIDE_VERSION`
- Split `APP_TITLE` into separate `APP_NAME` and `APP_VERSION` components
- Add `__all__` for explicit public exports
- Standardize on double quotes for string consistency
- Replace Unicode characters with ASCII equivalents for portability

### New Files
- `.gitignore`: Added for Python bytecode (`__pycache__/`, `*.pyc`) and IDE files

### Statistics
| File | Changes |
|------|---------|
| config.py | +165 lines, -104 lines |
| .gitignore | +18 lines (new) |

---

## PR #2: Improve export.py with Type Hints and Error Handling

### Changes to export.py
- Add comprehensive type hints throughout the module
- Replace bare `except:` clauses with specific exception types
- Add `ProfileData` TypedDict and `ParsedProfile` dataclass for better typing
- Add profile name validation and filename sanitization
- Add profile deletion capability with confirmation dialog
- Add configurable `max_profiles` display limit
- Add Delete key binding in profiles listbox
- Add proper encoding specification (`utf-8`) to all file operations
- Refactor duplicate profile parsing logic into `_parse_profile_file` helper
- Add `_format_profile_display` helper to eliminate code duplication
- Add `_get_selected_profile_path` helper for DRY principle
- Replace print statements with proper logging
- Add detailed docstrings with Args/Returns documentation
- Rename `self.logger` to `self.data_logger` to avoid confusion with module logger
- Add thousand separator to points count display

### Statistics
| File | Changes |
|------|---------|
| export.py | +508 lines, -211 lines |

---

## PR #3: Improve config.py Typing and Helpers

### Additional Changes to config.py
- Further improvements to type annotations
- Added helper functions for configuration access

### Statistics
| File | Changes |
|------|---------|
| config.py | +72 lines, -5 lines |

---

# Spindle Tuner v6.0 - Round 17 Bug Fixes

## Summary

This round fixed **5 confirmed bugs** identified with verifiable evidence from config.py.

---

# Spindle Tuner v6.0 - Round 18 export.py Improvements

## Proposal Review

**Proposed rewrite**: ~450 lines (+80% increase)
**Accepted improvements**: +86 lines (+34% increase)

### Breaking Change Identified

The proposal called `self.logger.export_csv(path, metadata=metadata, overwrite=overwrite)` but logger.py's `export_csv()` only accepts `filepath` - this would crash at runtime.

### Over-Engineering Rejected

| Feature | Lines | Reason |
|---------|-------|--------|
| `Profile` dataclass with schema versioning | ~50 | Simple JSON doesn't need migration |
| `ProfileStore` class | ~40 | Unnecessary abstraction |
| `_sanitize_profile_stem()` regex | ~10 | `replace(' ', '_')` is sufficient |
| Atomic writes via tempfile | ~15 | Marginal benefit for small files |
| logging module integration | ~10 | Console print is sufficient |

### Improvements Accepted

| Feature | Benefit |
|---------|---------|
| Recording button text sync | Shows "Resume" when paused, "Pause" when recording |
| Better profile list display | Shows "name — date" instead of just filename |
| "Load Selected" button | Explicit button in addition to double-click |
| "Open Folder" button | Quick access to profiles directory |
| Confirmation before loading | Prevents accidental parameter changes |
| Filter unknown parameters | Only applies params that exist in BASELINE_PARAMS |
| Save to File in INI dialog | Useful complement to Copy to Clipboard |
| Path tracking for profiles | Fixes Load Selected for new display format |

## Files Modified

- `export.py`: 251 → 338 lines (+87)

## Implementation Details

### Recording Button Sync
```python
# Now updates button text to match state
self.btn_record_toggle.config(text="Resume")  # when paused
self.btn_record_toggle.config(text="Pause")   # when recording
```

### Profile List Display
```python
# Before: just filename
"Conservative_20241201_143022.json"

# After: name + date
"Conservative — 2024-12-01 14:30"
```

### Profile Loading Confirmation
```python
msg = f"Load profile '{name}'?\n\n"
msg += f"Parameters: {len(known_params)}\n"
msg += f"Created: {profile.get('timestamp', 'Unknown')}\n\n"
msg += "This will update the current tuning parameters."

if not messagebox.askyesno("Load Profile", msg):
    return
```

### Unknown Parameter Filtering
```python
# Only apply parameters that exist in BASELINE_PARAMS
known_params = {k: v for k, v in params.items() if k in BASELINE_PARAMS}
```

## Verification

- Syntax check: `python3 -m py_compile export.py` ✓
- Line count: 338 lines (+87 from 251)

## Design Principles Followed

1. ✓ **Targeted improvements** - No full rewrite
2. ✓ **Minimal additions** - +86 lines vs proposed +200
3. ✓ **No breaking changes** - Doesn't change logger.py API
4. ✓ **Practical UX wins** - Button sync, confirmation, folder access


## Files Modified

- `config.py`: 1 change (-1 line net due to comment change)
- `dashboard.py`: 5 changes (+11 lines, 1326 → 1337)

## Bug Fixes Applied

### 1. Plot Time Scale vs Buffer Mismatch (config.py)

**Problem**: Dashboard offers time scales up to 120s (line 64: `TIME_SCALE_OPTIONS = [10, 30, 60, 120]`), but `HISTORY_DURATION_S = 30` means data for 60s and 120s views doesn't exist.

**Fix**:
```python
# Before
HISTORY_DURATION_S = 30   # Data buffer duration

# After  
HISTORY_DURATION_S = 120  # Data buffer duration (must cover max plot time scale)
```

### 2. Wrong Key for Safety Chain Status (dashboard.py)

**Problem**: Dashboard used `'external_ok'` key, but config.py defines `'safety_chain': 'external-ok'`. Result: status indicator always showed default value.

**Fix**: Changed indicator setup and update to use `'safety_chain'`:
- Line 329: `('external_ok', ...)` → `('safety_chain', ...)`
- Line 1170: `values.get('external_ok', 1)` → `values.get('safety_chain', 1.0)`
- Line 1180: `status_indicators['external_ok']` → `status_indicators['safety_chain']`

### 3. Direction Indicator Using Wrong Feedback (dashboard.py)

**Problem**: Direction detection used `values.get('feedback', 0)` which maps to `pid.s.feedback` - this is post-ABS and always positive, so CCW never displayed.

**Fix**: Use signed `feedback_raw` for direction logic:
```python
# Before
if abs(fb) < 10:
    self.lbl_direction.config(text="STOP", ...)
elif fb > 0:
    self.lbl_direction.config(text="CW →", ...)

# After
fb_raw = values.get('feedback_raw', fb)
if abs(fb_raw) < 10:
    self.lbl_direction.config(text="STOP", ...)
elif fb_raw > 0:
    self.lbl_direction.config(text="CW →", ...)
```

### 4. Double HAL Writes (dashboard.py)

**Problem**: When `live_apply=True`, `_on_slider_change()` called BOTH:
- `self.hal.set_param(param_name, val)` directly
- `self.on_param_change(param_name, val)` which in main.py also calls `hal.set_param()`

Result: Every slider change wrote to HAL twice.

**Fix**: Only call callback when NOT live applying:
```python
# Before
if self.live_apply.get():
    self.hal.set_param(param_name, val)
if self.on_param_change:
    self.on_param_change(param_name, val)

# After
if self.live_apply.get():
    self.hal.set_param(param_name, val)
elif self.on_param_change:  # Only callback when not live applying
    self.on_param_change(param_name, val)
```

### 5. UI Slider Values Not Snapped to Step (dashboard.py)

**Problem**: HAL's `_clamp_and_snap()` (Round 13) produces clean values like 0.05, 0.10, 0.15. But UI displayed/set unsnapped values like 0.0523, causing "what you see ≠ what you set" confusion.

**Fix**: Added `_snap_param()` helper matching HAL behavior:
```python
def _snap_param(self, param_name: str, value: float) -> float:
    """Snap parameter value to configured step (matches HAL's _clamp_and_snap)."""
    _, _, min_val, max_val, step, _, _ = TUNING_PARAMS[param_name]
    v = max(min_val, min(max_val, value))
    if step and step > 0:
        steps = round((v - min_val) / step)
        v = min_val + steps * step
        v = max(min_val, min(max_val, v))
    return v
```

Used in:
- `_on_slider_change()`: Snap before display/HAL write
- `_edit_param_value()`: Snap typed values

## Verification

All changes verified with `python3 -m py_compile`:
- config.py: Syntax OK (212 lines)
- dashboard.py: Syntax OK (1337 lines, +11 from 1326)

## Statistics

| File | Original | Updated | Delta |
|------|----------|---------|-------|
| config.py | 213 | 212 | -1 |
| dashboard.py | 1326 | 1337 | +11 |
| **Total** | 1539 | 1549 | **+10** |

## Design Principles Followed

1. ✓ **Fix real bugs** - All issues had verifiable evidence from config.py
2. ✓ **Minimal changes** - Only touched lines necessary for fixes
3. ✓ **Consistency** - UI snapping matches HAL `_clamp_and_snap()` from Round 13
4. ✓ **No new features** - Pure bug fixes, no scope creep
