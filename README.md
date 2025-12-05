# Spindle Tuner v6.0

[![CI](https://github.com/markmounteer/cnclatheSpindleTuner/actions/workflows/python-app.yml/badge.svg)](https://github.com/markmounteer/cnclatheSpindleTuner/actions/workflows/python-app.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LinuxCNC 2.8+](https://img.shields.io/badge/LinuxCNC-2.8+-green.svg)](https://linuxcnc.org/)

A comprehensive spindle PID tuning companion application for LinuxCNC, specifically designed for the Grizzly 7x14 CNC lathe conversion with closed-loop spindle control.

Based on **[Spindle PID Tuning Guide v5.3](SPINDLE_PID_TUNING_GUIDE_v5.3.md)**.

## Highlights

- **Real-time dashboard** with live RPM gauges, status indicators, and multi-trace plotting
- **Automated test procedures** for step response, load recovery, encoder verification, and more
- **Interactive troubleshooter** with decision trees for diagnosing common issues
- **Mock mode** for training and testing without hardware
- **Profile management** for saving/loading tuning configurations

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Baseline Parameters](#baseline-parameters)
- [Hardware Specifications](#hardware-specifications)
- [Troubleshooting Quick Reference](#troubleshooting-quick-reference)
- [Architecture](#architecture)
- [Safety Warnings](#safety-warnings)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Real-Time Dashboard

- **Live RPM Gauges**: Command, feedback, error, and integrator values
- **Status Indicators**: At-speed, watchdog, encoder health, spindle enable, safety chain
- **Multi-Trace Plot**: Real-time plotting with zoom/pan (matplotlib)
  - Configurable time scales: 10s, 30s, 60s, 120s
  - Toggle individual traces (command, feedback, error, integrator)
- **Parameter Tuning Sliders**: Adjust PID parameters with instant HAL updates
- **Quick Presets**: Conservative, Baseline (v5.3), Aggressive

### Automated Test Procedures

| Test | Purpose | Guide Section |
|------|---------|---------------|
| Step Response | Measure settling time and overshoot | §7.1 |
| Deceleration | Check stop behavior and braking | §7.1 |
| Full Ramp | Complete 0 → 1800 → 0 RPM cycle | §7.1 |
| Open Loop | Verify VFD scaling without PID feedback | §6.5 |
| Reverse Safety | Verify ABS component for M4 operation | §6.3 |
| Load Recovery | Measure response to cutting loads | §7.2 |
| Steady-State | Monitor thermal drift over time | §7.3 |
| Pre-Flight | Startup verification checklist | §5, §14.3 |
| Encoder Verification | Multi-speed accuracy test | §12.2 |

### Interactive Troubleshooter

Decision tree based on Guide §14.4 with color-coded severity:

- 🟠 **Orange**: Oscillation issues (fast/slow)
- 🟡 **Yellow**: Overshoot, load recovery, steady-state errors
- 🔴 **Red**: Critical issues (speed not reaching target, reverse runaway)

### Checklists

- **Hardware Verification** (10 items): Complete before first power-on
- **Commissioning Cleanup** (10 items): Complete before declaring tuning finished
- **Hardware Specs Reference**: Quick lookup for motor, VFD, encoder parameters

### Data Management

- **Continuous Recording**: Data logged at 10Hz update rate
- **CSV Export**: Export recorded data with metadata
- **Profile Save/Load**: JSON format with parameter snapshots
- **INI Generation**: Generate LinuxCNC config sections directly

---

## Requirements

### Software

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | With tkinter (usually included) |
| LinuxCNC | 2.8+ | For real HAL connection |
| matplotlib | Optional | Required for real-time plotting |

On Debian/Ubuntu systems, ensure tkinter is installed:

```bash
sudo apt-get install python3-tk
```

### Hardware (for target system)

| Component | Model | Purpose |
|-----------|-------|---------|
| Motor | Baldor M3558T (2HP) | 1750 RPM base speed |
| VFD | XSY-AT1 | 0-10V analog control |
| Encoder | ABILKEEN 1024 PPR | 4096 counts/rev, differential |
| Controller | Mesa 7i76E | Analog output + encoder input |

> **Note**: The application can run in mock mode without any hardware for training purposes.

---

## Installation

### Option 1: Install to LinuxCNC config directory

```bash
# Clone or copy to your LinuxCNC config directory
cp -r cnclatheSpindleTuner/ ~/linuxcnc/configs/Grizzly7x14_Lathe/spindle_tuner/

# Install optional dependencies
pip install matplotlib
```

### Option 2: Run from any location

```bash
# Clone the repository
git clone <repository-url>
cd cnclatheSpindleTuner

# Install optional dependencies
pip install matplotlib

# Run the application
python main.py --mock  # Test mode (no LinuxCNC required)
python main.py         # Real mode (requires LinuxCNC)
```

---

## Quick Start

### Mock Mode (Testing/Training)

Run without a LinuxCNC connection to explore the interface:

```bash
python main.py --mock
```

Mock mode features:
- Realistic physics simulation (VFD delay, motor slip, thermal drift)
- Fault simulation buttons (encoder fault, polarity reversed, DPLL disabled)
- Full UI functionality for training and testing

### Real Mode

Run connected to LinuxCNC:

```bash
python main.py
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--mock` | Run in mock mode without HAL connection |

Example:

```bash
python main.py          # Real mode (requires LinuxCNC)
python main.py --mock   # Mock mode (no hardware required)
```

---

## Usage Guide

### First-Time Setup

1. **Run Pre-Flight Check** (Tests tab → Pre-Flight Check)
   - Verifies DPLL timer, encoder scale, safety signals
2. **Complete Hardware Verification Checklist** (Checklists tab)
   - 10-item checklist covering wiring, VFD settings, safety
3. **Run Reverse Safety Test**
   - Verify ABS component prevents M4 runaway
4. **Run Encoder Verification**
   - Test accuracy at multiple speeds

### Tuning Session Workflow

1. Start with **Baseline** preset (Presets menu)
2. Run **Step Response Test** (F5)
3. Use **Troubleshooter** if issues detected
4. Adjust parameters incrementally via sliders
5. Run **Load Recovery Test** for real-world performance
6. **Save profile** when satisfied (Ctrl+S)

### Threading Preparation

1. Navigate to Tests tab → Threading section
2. Check revolutions display increments smoothly
3. Reset counter and verify it resets correctly
4. Verify at-speed indicator functions properly

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **File Operations** | |
| Ctrl+N | New session (clear data) |
| Ctrl+O | Load profile |
| Ctrl+S | Save profile |
| Ctrl+E | Export CSV |
| Ctrl+Q | Quit application |
| **Navigation** | |
| Ctrl+1-5 | Switch to tab 1-5 |
| Ctrl+PgUp/PgDn | Previous/next tab |
| **Spindle Control** | |
| F5 | Run step test |
| F8 | Run full test suite |
| Space | Toggle spindle on/off |
| Escape | Emergency stop |

---

## Baseline Parameters

Baseline parameters from Tuning Guide v5.3:

| Parameter | Value | Description |
|-----------|-------|-------------|
| P | 0.1 | Proportional gain (keep low for VFD) |
| I | 1.0 | Integral gain (slip compensation) |
| D | 0.0 | Derivative gain (usually 0 for spindle) |
| FF0 | 1.0 | Feedforward velocity (primary control) |
| FF1 | 0.35 | Feedforward acceleration |
| Deadband | 10 | Error deadband in RPM |
| MaxErrorI | 60 | Integrator windup limit |
| MaxCmdD | 1200 | Command derivative limit |
| RateLimit | 1200 | Command rate limit (RPM/s) |
| FilterGain | 0.5 | Velocity filter gain |

### Presets

| Preset | Use Case | Key Differences |
|--------|----------|-----------------|
| **Conservative** | Initial testing, problematic setups | Lower P (0.05), higher deadband (15) |
| **Baseline** | Standard operation, v5.3 recommended | Default values as above |
| **Aggressive** | Fast response, stable systems | Higher P (0.15), I (1.2), lower deadband (8) |

---

## Hardware Specifications

### Motor: Baldor M3558T

| Spec | Value |
|------|-------|
| Power | 2 HP |
| Base Speed | 1750 RPM |
| Sync Speed | 1800 RPM |
| Cold Slip | 2.7% |
| Hot Slip | 3.6% |
| Thermal Time Constant | 20 minutes |

### VFD: XSY-AT1

| Spec | Value |
|------|-------|
| Accel Time | 1.5s |
| Decel Time | 1.5s |
| Max Frequency | 65 Hz |
| Transport Delay | ~1.5s |

### Encoder: ABILKEEN 1024 PPR

| Spec | Value |
|------|-------|
| Counts/Rev | 4096 (quadrature) |
| Type | Differential |
| DPLL Timer | +100 µs |

---

## Troubleshooting Quick Reference

| Symptom | First Steps |
|---------|-------------|
| **Fast oscillation (>1 Hz)** | Reduce P-gain to 0.05, increase deadband to 15-20 |
| **Slow oscillation (0.1-0.5 Hz)** | Disable VFD torque boost (P72=0), reduce I-gain |
| **Overshoot on speed changes** | Reduce FF1 to 0.3, check RateLimit |
| **Slow load recovery (>2s)** | Increase I-gain to 1.2-1.5, increase MaxErrorI |
| **Speed not reaching target** | Check VFD P0.04 ≥ 62 Hz, verify VFD_SCALE |
| **Hunting at low speed** | Increase deadband, verify DPLL configured |
| **No encoder counts** | Check wiring, verify 5V power, try filter=0 |
| **Reverse runaway (M4)** | Verify ABS component in signal path |

See the **Troubleshooter** tab for detailed decision trees.

---

## Architecture

```
cnclatheSpindleTuner/
├── main.py                 # Application entry point, UI wiring, update loop
├── config.py               # Constants, HAL pins, baseline parameters, presets
├── hal_interface.py        # HAL interface, mock mode simulation, INI handling
├── logger.py               # Data recording, metrics, CSV export
├── dashboard.py            # Dashboard tab: gauges, plot, parameter sliders
├── troubleshooter.py       # Troubleshooter tab: symptom decision tree
├── export.py               # Export tab: profiles, CSV export, INI generation
├── tests/                  # Tests tab module
│   ├── tests_tab.py        # Main tests tab UI
│   ├── checklists_tab.py   # Hardware verification checklists
│   ├── base.py             # Base test class
│   └── test_*.py           # Individual test implementations
├── tests_pytest/           # Pytest-based unit tests
│   ├── conftest.py         # Test fixtures
│   └── test_*.py           # Unit test files
├── test_smoke.py           # CI smoke tests
├── SPINDLE_PID_TUNING_GUIDE_v5.3.md  # Complete tuning reference
├── CHANGELOG.md            # Version history and bug fixes
└── README.md               # This file
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `main.py` | Application bootstrap, tab creation, update loop (10Hz), keyboard shortcuts |
| `config.py` | All configuration: HAL pin mappings, tuning parameters, hardware specs, troubleshooting data |
| `hal_interface.py` | HAL communication abstraction, mock mode physics simulation, connection management |
| `logger.py` | Circular buffer data storage, metrics calculation, CSV export |
| `dashboard.py` | Real-time visualization, parameter adjustment UI, status indicators |
| `tests/` | Automated test sequences, checklist UI, threading tools |
| `troubleshooter.py` | Symptom-based diagnosis interface |
| `export.py` | Profile management, data export, INI config generation |

---

## Safety Warnings

> **Keep E-stop within reach at all times when running tests**

> **Reverse Safety Test (M4) can cause runaway if ABS component is missing - verify before testing**

> **Never exceed P-gain > 0.3 on VFD-controlled spindles**

> **Complete Hardware Verification Checklist before first powered operation**

> **Encoder Watchdog Test should be performed with workpiece removed**

---

## Development

### Running Tests

Lightweight pytest-based checks live in `tests_pytest/` alongside the application-specific test classes in `tests/`.

```bash
# Run the fast validation suite
pytest

# Run with verbose output
pytest -v

# Run only smoke tests (used in CI)
pytest test_smoke.py -v
```

The tests exercise:
- Module importability
- Configuration sanity (baseline/preset ranges, pin mapping uniqueness)
- HAL helper behaviors in mock mode

### Code Quality

The project uses flake8 for linting:

```bash
# Check for syntax errors and undefined names
flake8 . --select=E9,F63,F7,F82 --show-source

# Full lint check
flake8 . --max-line-length=127
```

### Mock Mode Development

Mock mode provides a realistic simulation environment for development:

```bash
python main.py --mock
```

Features available in mock mode:
- Physics simulation (VFD delay, motor slip, thermal drift)
- Fault injection buttons (encoder fault, polarity reversed, DPLL disabled)
- Full UI functionality without hardware

---

## Contributing

Contributions and suggestions welcome. The modular architecture makes it easy to extend:

| To Add | Modify |
|--------|--------|
| New test procedures | `tests/test_*.py` (create new file based on `tests/base.py`) |
| Troubleshooter entries | `config.py` → `SYMPTOM_DIAGNOSIS` |
| HAL pins | `config.py` → `MONITOR_PINS`, `TUNING_PARAMS` |
| Presets | `config.py` → `PRESETS` |
| Hardware specs | `config.py` → `*_SPECS` dictionaries |

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and run tests: `pytest`
4. Commit with descriptive messages
5. Push and create a pull request

---

## Acknowledgments

- Based on the [Spindle PID Tuning Guide v5.3](SPINDLE_PID_TUNING_GUIDE_v5.3.md)
- Designed for the Grizzly 7x14 CNC lathe conversion community
- See [CHANGELOG.md](CHANGELOG.md) for version history

---

## License

This software is provided as-is for educational and personal use with the Grizzly 7x14 CNC lathe conversion project.
