#!/usr/bin/env python3
"""
Spindle Tuner - Configuration Constants

All global constants, HAL pin mappings, tuning parameters, and hardware specifications.
Based on Spindle PID Tuning Guide v5.3.
"""

from pathlib import Path

# ==============================================================================
# APPLICATION CONSTANTS
# ==============================================================================

APP_TITLE = "Grizzly 7x14 Spindle Tuner v6.0"
APP_VERSION = "6.0"
UPDATE_INTERVAL_MS = 100  # 10Hz update rate
HISTORY_DURATION_S = 120  # Data buffer duration (must cover max plot time scale)

# File paths
DEFAULT_CONFIG_DIR = Path.home() / "linuxcnc" / "configs" / "Grizzly7x14_Lathe"
PROFILES_DIR = Path.home() / ".spindle_tuner_profiles"

# ==============================================================================
# HAL PIN MAPPINGS
# ==============================================================================

# Pins to monitor (read-only)
MONITOR_PINS = {
    'cmd_raw':       'spindle-vel-cmd-rpm-raw',
    'cmd_limited':   'spindle-vel-cmd-rpm-limited',
    'feedback':      'pid.s.feedback',
    'feedback_raw':  'spindle-vel-fb-rpm',
    'feedback_abs':  'spindle-vel-fb-rpm-abs',
    'output':        'pid.s.output',
    'error':         'pid.s.error',
    'errorI':        'pid.s.errorI',
    'at_speed':      'spindle-is-at-speed',
    'watchdog':      'encoder-watchdog-is-armed',
    'encoder_fault': 'encoder-fault',
    'spindle_on':    'spindle-enable',
    'spindle_revs':  'spindle.0.revs',
    # Pre-flight check pins
    'dpll_timer':    'hm2_7i76e.0.dpll.01.timer-us',
    'safety_chain':  'external-ok',
    'encoder_scale': 'hm2_7i76e.0.encoder.00.scale',
}

# Tuning parameters (writable)
# Format: param_name: (hal_pin, description, min, max, step, ini_section, ini_key)
TUNING_PARAMS = {
    'P':         ('pid.s.Pgain',              'Proportional gain',         0.0,   1.0,  0.01, 'SPINDLE_0', 'P'),
    'I':         ('pid.s.Igain',              'Integral gain',             0.0,   5.0,  0.1,  'SPINDLE_0', 'I'),
    'D':         ('pid.s.Dgain',              'Derivative gain',           0.0,   1.0,  0.1,  'SPINDLE_0', 'D'),
    'FF0':       ('pid.s.FF0',                'Feedforward (velocity)',    0.0,   2.0,  0.01, 'SPINDLE_0', 'FF0'),
    'FF1':       ('pid.s.FF1',                'Feedforward (accel)',       0.0,   1.0,  0.01, 'SPINDLE_0', 'FF1'),
    'Deadband':  ('pid.s.deadband',           'Error deadband (RPM)',      0.0,  50.0,  1.0,  'SPINDLE_0', 'DEADBAND'),
    'MaxErrorI': ('pid.s.maxerrorI',          'Integrator limit',          0.0, 200.0,  5.0,  'SPINDLE_0', 'MAX_ERROR_I'),
    'MaxCmdD':   ('pid.s.maxcmdD',            'Command derivative limit',  0.0, 5000.0, 100.0,'SPINDLE_0', 'MAX_CMD_D'),
    'RateLimit': ('spindle-cmd-limit.maxv',   'Rate limit (RPM/s)',      100.0, 3000.0, 50.0, 'SPINDLE_0', 'RATE_LIMIT'),
    'FilterGain':('spindle-vel-filter.gain',  'Filter gain',               0.1,   1.0,  0.05, 'SPINDLE_0', 'FILTER_GAIN'),
}

# ==============================================================================
# BASELINE PARAMETERS (v5.3 Guide)
# ==============================================================================

BASELINE_PARAMS = {
    'P':         0.1,
    'I':         1.0,
    'D':         0.0,
    'FF0':       1.0,
    'FF1':       0.35,
    'Deadband':  10.0,
    'MaxErrorI': 60.0,
    'MaxCmdD':   1200.0,
    'RateLimit': 1200.0,
    'FilterGain': 0.5,
}

# Tuning presets
PRESETS = {
    'conservative': {
        'P': 0.05, 'I': 0.8, 'FF1': 0.30,
        'Deadband': 15.0, 'MaxErrorI': 50.0, 'RateLimit': 1000.0,
    },
    'baseline': BASELINE_PARAMS.copy(),
    'aggressive': {
        'P': 0.15, 'I': 1.2, 'FF1': 0.40,
        'Deadband': 8.0, 'MaxErrorI': 80.0, 'RateLimit': 1200.0,
    },
}

# ==============================================================================
# HARDWARE SPECIFICATIONS
# ==============================================================================

MOTOR_SPECS = {
    'name': 'Baldor M3558T',
    'power_hp': 2.0,
    'base_speed_rpm': 1750,
    'sync_speed_rpm': 1800,
    'cold_slip_pct': 2.7,
    'hot_slip_pct': 3.6,
    'thermal_time_const_min': 20,
}

VFD_SPECS = {
    'name': 'XSY-AT1',
    'accel_time_s': 1.5,
    'decel_time_s': 1.5,
    'max_freq_hz': 65,
    'transport_delay_s': 1.5,
}

ENCODER_SPECS = {
    'name': 'ABILKEEN 1024 PPR',
    'counts_per_rev': 4096,
    'differential': True,
    'dpll_timer_us': -100,
}

# ==============================================================================
# TROUBLESHOOTER DATA
# ==============================================================================

SYMPTOM_DIAGNOSIS = [
    ("Fast Oscillation (>1 Hz)", 
     "• Reduce P-gain (try 0.05)\n• Increase DEADBAND (try 15-20)\n• Check VFD torque boost is OFF (P72=0)",
     "orange"),
    ("Slow Oscillation (0.1-0.5 Hz)",
     "• Disable VFD torque boost (P72=0)\n• Reduce I-gain (try 0.8)\n• Verify limit2 is working (check signals)",
     "orange"),
    ("Overshoot on Speed Changes",
     "• Verify limit2.maxv matches VFD accel time\n• Reduce FF1 (try 0.3)\n• Check RateLimit = 1800 / VFD_accel_seconds",
     "yellow"),
    ("Slow Load Recovery (>2s)",
     "• Increase I-gain (try 1.2-1.5)\n• Increase MaxErrorI proportionally\n• Check VFD slip compensation setting",
     "yellow"),
    ("Speed Not Reaching Target",
     "• Check VFD P0.04 ≥ 62 Hz\n• Verify VFD_SCALE matches motor\n• Check MaxErrorI allows enough correction\n• Verify analog output reaches VFD",
     "red"),
    ("Steady-State Error (±10+ RPM)",
     "• Increase I-gain slightly\n• Reduce DEADBAND if too high\n• Check encoder scale is correct (4096)",
     "yellow"),
    ("Hunting at Low Speed (<200 RPM)",
     "• Increase DEADBAND (try 15-20)\n• Check DPLL is configured\n• Verify encoder vel-timeout = 0.1",
     "orange"),
    ("Unexpected Realtime Delay",
     "• Run latency-histogram test\n• Disable CPU frequency scaling\n• Check for competing processes\n• Consider isolcpus kernel parameter",
     "orange"),
    ("No Encoder Counts",
     "• Check encoder wiring (A, B, Z, 5V, GND)\n• Verify 5V power at encoder\n• Try filter=0 temporarily\n• Check Mesa encoder counter increment",
     "red"),
    ("VFD Faults on Start",
     "• Increase VFD accel time to 2-3s\n• Reduce FF1 (try 0.25)\n• Check for overcurrent (motor wiring)\n• Verify VFD current limit settings",
     "red"),
    ("Integrator Windup",
     "• Reduce MaxErrorI to 50\n• Verify limit2 is active (check signal path)\n• Check for large sustained errors\n• Consider adding error deadband",
     "yellow"),
    ("Reverse Runaway (M4)",
     "• Verify ABS component in signal path\n• Check spindle-vel-fb-rpm-abs always positive\n• Test with M4 S100 and monitor feedback\n• Fix encoder polarity if needed",
     "red"),
]

# ==============================================================================
# CHECKLIST DATA
# ==============================================================================

HARDWARE_CHECKLIST = [
    ("encoder_jumpers", "Mesa 7i76E encoder jumpers W10, W11, W13 = RIGHT position (differential mode)"),
    ("encoder_shield", "Encoder cable shield grounded at Mesa end ONLY (not at encoder)"),
    ("cable_routing", "Encoder cables routed ≥6\" away from VFD power cables"),
    ("vfd_analog", "VFD analog input verified: 0V=0 RPM, 10V=1800 RPM"),
    ("mesa_leds", "Mesa 7i76E LEDs: Green=solid, Red=blinking (normal operation)"),
    ("estop_wired", "E-stop properly wired and cuts ALL power (spindle, drives)"),
    ("encoder_5v", "Encoder 5V power verified at encoder connector"),
    ("vfd_params", "VFD parameters set: P0.04≥62Hz, P0.11=1.5s accel, P72=0 (no torque boost)"),
    ("spindle_free", "Spindle rotates freely by hand (no binding or rubbing)"),
    ("work_area", "Work area clear, safety glasses on, no loose clothing"),
]

COMMISSIONING_CHECKLIST = [
    ("soft_limits", "Soft limits configured and tested (prevent crashes at travel extremes)"),
    ("estop_tested", "E-stop tested: cuts all motion AND spindle immediately"),
    ("encoder_watchdog", "Encoder watchdog tested: E-stops within 1s when encoder disconnected"),
    ("vfd_fault", "VFD fault triggers E-stop (test by inducing overcurrent or other fault)"),
    ("servo_fault", "Servo/stepper fault triggers E-stop"),
    ("bypass_removed", "Any drives-ok bypasses REMOVED from custom.hal"),
    ("pid_stable", "PID tuning stable: no oscillation, good load recovery, thermal tracking"),
    ("threading_tested", "Threading tested if applicable (index pulse, at-speed tolerance)"),
    ("config_backed_up", "Final configuration saved and backed up (INI, HAL files, this profile)"),
    ("documentation", "Changes documented (what parameters changed from defaults, why)"),
]

# ==============================================================================
# PLOT CONFIGURATION
# ==============================================================================

PLOT_TRACES = {
    'cmd':      {'color': 'blue',   'label': 'Command'},
    'feedback': {'color': 'green',  'label': 'Feedback'},
    'error':    {'color': 'red',    'label': 'Error'},
    'errorI':   {'color': 'orange', 'label': 'Integrator'},
}

PLOT_DEFAULTS = {
    'cmd': True,
    'feedback': True,
    'error': True,
    'errorI': False,
}
