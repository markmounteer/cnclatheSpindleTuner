# Potential Features - Enhancement Suggestions

This file documents potential improvements identified during code review. These are not errors and should not be implemented without explicit approval.

---

## dashboard.py

### 1. Speed Entry Field Validation

- **Current state**: Line 441 - Speed entry accepts any text input; validation only happens when attempting to convert to int (lines 1266-1269, 1280-1281)
- **Suggested enhancement**: Add input validation to prevent non-numeric characters from being entered in the speed entry field
- **Rationale**: Would provide immediate feedback to users rather than silently failing or defaulting to 1000 RPM
- **Implementation considerations**: Could use `validatecommand` with `%P` substitution or bind to `KeyRelease` events; need to consider paste operations

### 2. Dynamic Plot Trace Label

- **Current state**: Line 523 - Plot mode label is hardcoded to "Plot: Command, Feedback, Error, Integrator"
- **Suggested enhancement**: Update the label dynamically based on which traces are actually visible
- **Rationale**: Would accurately reflect current plot state and help users understand what they're viewing
- **Implementation considerations**: Would need to update label in `_update_trace_visibility()` method; consider performance if called frequently

### 3. Fallback Chart Error Trace Scaling

- **Current state**: Lines 1016-1020 - Error trace is scaled by 5x and centered at 1000 RPM for visibility in the canvas fallback chart
- **Suggested enhancement**: Add a separate Y-axis or legend indicator for error scale in fallback mode
- **Rationale**: The current 5x scaling may confuse users who don't realize error values are magnified
- **Implementation considerations**: Would require additional canvas elements; need to maintain simplicity for systems without matplotlib

### 4. Keyboard Shortcut Help Overlay

- **Current state**: Lines 1143-1156 - Keyboard shortcuts exist (Space=stop, F5=step test, 1-4=speed presets) but are only documented in module docstring
- **Suggested enhancement**: Add a help button or tooltip that shows available keyboard shortcuts
- **Rationale**: Discoverability - users may not know these shortcuts exist
- **Implementation considerations**: Could be a simple button that shows a messagebox or tooltip; minimal code addition

### 5. Error History Export

- **Current state**: Statistics panel (lines 404-430) tracks error history but only displays aggregated stats
- **Suggested enhancement**: Add option to export raw error history data for external analysis
- **Rationale**: Advanced users may want to perform custom analysis on error patterns
- **Implementation considerations**: Could add export button to stats panel; consider memory implications of larger history buffers
