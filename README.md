# Spindle Tuner v6.0

A comprehensive spindle PID tuning companion application for LinuxCNC, specifically designed for the Grizzly 7x14 CNC lathe conversion with closed-loop spindle control.

Based on **Spindle PID Tuning Guide v5.3**.

## Features

### Real-Time Dashboard
- Live RPM gauges (command, feedback, error, integrator)
- Status indicators (at-speed, watchdog, encoder, spindle enable)
- Multi-trace plot with zoom/pan (matplotlib)
- Parameter tuning sliders with instant HAL updates
- Quick presets (Conservative, Baseline, Aggressive)

### Automated Test Procedures
| Test | Purpose | Guide Section |
|------|---------|---------------|
| Step Response | Measure settling time, overshoot | §7.1 |
| Deceleration | Check stop behavior | §7.1 |
| Full Ramp | 0→1800→0 RPM cycle | §7.1 |
| Open Loop | Verify VFD scaling without PID | §6.5 |
| Reverse Safety | Verify ABS component for M4 | §6.3 |
| Load Recovery | Measure response to cutting loads | §7.2 |
| Steady-State | Monitor thermal drift over time | §7.3 |
| Pre-Flight | Startup verification checklist | §5, §14.3 |
| Encoder Verification | Multi-speed accuracy test | §12.2 |

### Interactive Troubleshooter
Decision tree based on Guide §14.4 with color-coded severity:
- 🟠 Fast/slow oscillation solutions
- 🟡 Overshoot and load recovery fixes
- 🔴 Critical issues (speed not reaching, reverse runaway)

### Checklists
- **Hardware Verification** (10 items) - Complete before first power-on
- **Commissioning Cleanup** (10 items) - Complete before declaring tuning finished
- **Hardware Specs Reference** - Quick lookup for motor, VFD, encoder parameters

### Data Management
- Continuous data recording with CSV export
- Profile save/load (JSON format)
- INI section generation for LinuxCNC config

## Installation

### Requirements
- Python 3.8+
- LinuxCNC (for real operation) or use `--mock` for testing
- matplotlib (optional, for plotting)

### Setup
```bash
# Copy to your LinuxCNC config directory
cp -r spindle_tuner/ ~/linuxcnc/configs/Grizzly7x14_Lathe/

# Run in mock mode (no LinuxCNC required)
python spindle_tuner/main.py --mock

# Run with real HAL connection
python spindle_tuner/main.py
```

## File Structure

```
spindle_tuner/
├── main.py           # Application entry point
├── config.py         # Constants, HAL pins, baseline parameters
├── hal.py            # HAL interface & INI handling
├── logger.py         # Data logging & metrics
├── dashboard.py      # Dashboard UI slice
├── tests.py          # Tests & checklists UI slice
├── troubleshooter.py # Decision tree UI slice
├── export.py         # Export & profiles UI slice
├── README.md         # This file
└── CHANGELOG.md      # Version history
```

## Usage

### First-Time Setup
1. Run Pre-Flight Check (Tests tab → Pre-Flight Check)
2. Complete Hardware Verification Checklist (Checklists tab)
3. Run Reverse Safety Test to verify ABS component
4. Run Encoder Verification at multiple speeds

### Tuning Session
1. Start with Baseline preset
2. Run Step Response Test (F5)
3. Use Troubleshooter if issues detected
4. Adjust parameters incrementally
5. Run Load Recovery Test for real-world performance
6. Save profile when satisfied

### Before Threading
1. Check revolutions display (Tests tab → Threading section)
2. Verify revs counter increments smoothly
3. Reset and verify it resets correctly

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Ctrl+O | Load profile |
| Ctrl+S | Save profile |
| Ctrl+E | Export CSV |
| F5 | Run step test |
| Space | Toggle spindle on/off |
| Escape | Emergency stop |

## Baseline Parameters (v5.3)

| Parameter | Value | Purpose |
|-----------|-------|---------|
| P | 0.1 | Proportional gain (keep low for VFD) |
| I | 1.0 | Integral gain (slip compensation) |
| D | 0.0 | Derivative gain (usually 0) |
| FF0 | 1.0 | Feedforward velocity (main control) |
| FF1 | 0.35 | Feedforward acceleration |
| Deadband | 10 | Error deadband (RPM) |
| MaxErrorI | 60 | Integrator limit |
| RateLimit | 1200 | Command rate limit (RPM/s) |

## Mock Mode

Run with `--mock` flag to test without LinuxCNC connection:
```bash
python main.py --mock
```

Mock mode features:
- Realistic physics simulation (VFD delay, motor slip, thermal drift)
- Fault simulation buttons (encoder fault, polarity reversed, DPLL disabled)
- Full UI functionality for training/testing

## Hardware Specifications

| Component | Model | Key Specs |
|-----------|-------|-----------|
| Motor | Baldor M3558T | 2HP, 1750 RPM, 2.7-3.6% slip |
| VFD | XSY-AT1 | 1.5s accel, ~1.5s transport delay |
| Encoder | ABILKEEN 1024 PPR | 4096 counts/rev, differential |
| Controller | Mesa 7i76E | Analog spindle output, encoder input |

## Safety Warnings

⚠️ **Always keep E-stop within reach when running tests**

⚠️ **Reverse Safety Test (M4) can cause runaway if ABS component is missing**

⚠️ **Encoder Watchdog Test should be performed with caution**

⚠️ **Never exceed P-gain > 0.3 on VFD-controlled spindles**

## License

This software is provided as-is for educational and personal use with the Grizzly 7x14 CNC lathe conversion project.

## Contributing

Suggestions and improvements welcome. The modular architecture makes it easy to add new features:
- Add tests in `tests.py`
- Add troubleshooter entries in `config.py` (SYMPTOM_DIAGNOSIS)
- Add HAL pins in `config.py` (MONITOR_PINS, TUNING_PARAMS)
