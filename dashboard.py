#!/usr/bin/env python3

"""
Spindle Tuner - Dashboard Feature

Main dashboard with live gauges, real-time plot, and parameter tuning controls.

Improvements in this version:
- Statistics panel showing min/max/avg error
- Direction indicator (CW/CCW/STOP)
- PID output and VFD % displays
- Color-coded error based on magnitude
- Plot pause/resume and time scale controls
- Read from HAL / Reset to Baseline buttons
- Live apply mode for immediate parameter changes
- Keyboard shortcuts (F5=step test, Space=stop)
- Enhanced plot with dual y-axis option
- Screenshot export for plots
- Blitting optimization for Raspberry Pi performance
- Revs gauge for threading operations (§10.2)
- Text fallback mode for systems without matplotlib
- Visual RPM bars for slip monitoring
- Bidirectional error meter (Canvas-based)
- Precision parameter editing (click value to type)
- Individual parameter reset (right-click context menu)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Any, Dict, Callable, Optional, List
from collections import deque
from datetime import datetime
import time
import csv

from config import (
    TUNING_PARAMS, BASELINE_PARAMS, PRESETS,
    PLOT_TRACES, PLOT_DEFAULTS, HISTORY_DURATION_S,
)

# Matplotlib imports
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Error thresholds for color coding (RPM)
ERROR_THRESHOLD_EXCELLENT = 10
ERROR_THRESHOLD_GOOD = 25
ERROR_THRESHOLD_WARNING = 50
ERROR_THRESHOLD_CRITICAL = 100

# Time scale options for plot (seconds)
TIME_SCALE_OPTIONS = [10, 30, 60, 120]

# Statistics window (seconds)
STATS_WINDOW_S = 5.0


# =============================================================================
# TOOLTIP CLASS
# =============================================================================

class Tooltip:
    """Simple tooltip for widgets."""
    
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self._show)
        self.widget.bind("<Leave>", self._hide)
    
    def _show(self, event=None):
        """Show tooltip near widget."""
        # Destroy any existing tooltip to prevent orphaned windows
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            bg="lightyellow",
            relief="solid",
            bd=1,
            padx=3,
            pady=3,
        )
        label.pack()
    
    def _hide(self, event=None):
        """Hide tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# =============================================================================
# DASHBOARD TAB
# =============================================================================

class DashboardTab:
    """
    Enhanced dashboard feature slice.
    
    Provides:
    - Live RPM gauges with color-coded error
    - Direction indicator (CW/CCW/STOP)
    - PID output and VFD % displays
    - Statistics panel (min/max/avg)
    - Status indicators (at-speed, watchdog, encoder)
    - Real-time multi-trace plot with zoom/pan
    - Plot pause/resume and time scale controls
    - Parameter tuning sliders with groups
    - Quick presets and keyboard shortcuts
    - Read from HAL / Reset to Baseline buttons
    """
    
    def __init__(self, parent: ttk.Frame, hal_interface, data_logger,
                 on_param_change: Optional[Callable] = None):
        """
        Initialize dashboard tab.
        
        Args:
            parent: Parent frame to build UI in
            hal_interface: HalInterface instance
            data_logger: DataLogger instance
            on_param_change: Callback when parameter changes
        """
        self.parent = parent
        self.hal = hal_interface
        self.logger = data_logger
        self.on_param_change = on_param_change
        
        # Parameter tracking
        self.param_vars: Dict[str, tk.DoubleVar] = {}
        self.param_labels: Dict[str, ttk.Label] = {}
        self.param_scales: Dict[str, ttk.Scale] = {}  # For lock/unlock control
        self.live_apply = tk.BooleanVar(value=True)
        self.params_locked = tk.BooleanVar(value=False)

        # Plot state
        self.show_traces: Dict[str, tk.BooleanVar] = {}
        self.figure = None
        self.ax = None
        self.ax2 = None  # Secondary y-axis for error
        self.canvas = None
        self.lines: Dict[str, "Line2D"] = {}  # String annotation for conditional import
        self.plot_paused = False
        self.btn_pause = None
        self.time_scale = tk.IntVar(value=int(HISTORY_DURATION_S))
        self.dual_axis = tk.BooleanVar(value=False)

        # Blitting optimization state (for Raspberry Pi performance)
        self.background = None  # Cached plot background for blitting
        self.plot_dirty = False  # Flag to request full redraw

        # Text fallback for no-matplotlib systems
        self.text_fallback = None

        # Canvas-based fallback chart (when matplotlib unavailable)
        self.fallback_chart = None
        self.fallback_chart_data: deque = deque(maxlen=300)  # 30 seconds at 10Hz
        self.btn_pause_fallback = None
        self.fallback_traces: Dict[str, tk.BooleanVar] = {}
        self.fallback_labels: Dict[str, ttk.Label] = {}
        self.fallback_bar_canvas = None

        # Visual bars for glanceability
        self.bar_cmd = None
        self.bar_fb = None
        self.bar_error_canvas = None
        self.bar_error_rect = None

        # Statistics tracking
        self.error_history: deque = deque(maxlen=int(STATS_WINDOW_S * 10))
        self.stats_labels: Dict[str, ttk.Label] = {}
        self.session_peak_error = 0.0  # Persistent peak error (reset only manually)

        # Last known values for direction detection
        self.last_feedback = 0.0
        self.last_cmd = 0.0

        # Status message for user feedback
        self.status_message = None

        # Build UI
        self._setup_ui()
        self._setup_keyboard_shortcuts()

    @staticmethod
    def _coerce_float(value: Any, default: float = 0.0) -> float:
        """Safely convert a value to float for numeric widgets."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get_param_meta(param_name: str):
        """Return parameter metadata with safe defaults for legacy configs."""
        defaults = ("", "", 0.0, 0.0, 0.0, "", "")
        meta = TUNING_PARAMS.get(param_name)

        if meta is None:
            return defaults

        try:
            seq = list(meta)
        except TypeError:
            return defaults

        filled = list(defaults)
        for i, val in enumerate(seq[:len(filled)]):
            filled[i] = val
        return tuple(filled)
    
    # =========================================================================
    # UI SETUP
    # =========================================================================
    
    def _setup_ui(self):
        """Build the dashboard UI."""
        # Main split: left (plot + stats) / right (telemetry + params)
        main_paned = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(main_paned)
        right = ttk.Frame(main_paned)

        main_paned.add(left, weight=3)
        main_paned.add(right, weight=2)

        # LEFT: plot on top, stats below
        plot_frame = ttk.Frame(left)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        stats_frame = ttk.Frame(left)
        stats_frame.pack(fill=tk.X, pady=(5, 0))

        self._setup_plot(plot_frame)
        self._setup_statistics(stats_frame)

        # RIGHT: gauges + status + quick controls stacked, parameters fill rest
        right_top = ttk.Frame(right)
        right_top.pack(fill=tk.X)
        self._setup_gauges(right_top)
        self._setup_status(right_top)
        self._setup_quick_controls(right_top)

        self._setup_parameters(right)

        # Status message bar at bottom
        self.status_message = ttk.Label(self.parent, text="", foreground="blue",
                                         font=("Arial", 9))
        self.status_message.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
    
    def _setup_gauges(self, parent: ttk.Frame):
        """Setup RPM gauge displays with visual bars and error meter."""
        frame = ttk.LabelFrame(parent, text="Spindle", padding=5)
        frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Direction:").pack(side=tk.LEFT)
        self.lbl_direction = ttk.Label(
            top, text="STOP", font=("Arial", 11, "bold"), foreground="gray"
        )
        self.lbl_direction.pack(side=tk.LEFT, padx=4)

        self.lbl_spindle_state = ttk.Label(
            top, text="DISABLED", font=("Arial", 9, "bold"), foreground="red"
        )
        self.lbl_spindle_state.pack(side=tk.RIGHT)

        # Command RPM
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(cmd_frame, text="Cmd:", width=8).pack(side=tk.LEFT)
        self.lbl_cmd = ttk.Label(cmd_frame, text="0",
                                  font=("Courier", 16, "bold"), foreground="blue", width=6)
        self.lbl_cmd.pack(side=tk.LEFT)

        # Feedback RPM
        fb_frame = ttk.Frame(frame)
        fb_frame.pack(fill=tk.X)
        ttk.Label(fb_frame, text="Act:", width=8).pack(side=tk.LEFT)
        self.lbl_feedback = ttk.Label(fb_frame, text="0",
                                       font=("Courier", 16, "bold"), foreground="green", width=6)
        self.lbl_feedback.pack(side=tk.LEFT)

        # Visual RPM progress bars for slip monitoring
        bars_frame = ttk.Frame(frame)
        bars_frame.pack(fill=tk.X, pady=(2, 5))
        self.bar_cmd = ttk.Progressbar(bars_frame, orient=tk.HORIZONTAL, length=140,
                                        mode='determinate', maximum=2000)
        self.bar_cmd.pack(fill=tk.X, pady=1)
        self.bar_fb = ttk.Progressbar(bars_frame, orient=tk.HORIZONTAL, length=140,
                                       mode='determinate', maximum=2000)
        self.bar_fb.pack(fill=tk.X, pady=1)

        # Error with color coding
        err_frame = ttk.Frame(frame)
        err_frame.pack(fill=tk.X)
        ttk.Label(err_frame, text="Error:", width=8).pack(side=tk.LEFT)
        self.lbl_error = ttk.Label(err_frame, text="0.0",
                                    font=("Courier", 14), foreground="green", width=7)
        self.lbl_error.pack(side=tk.LEFT)

        # Bidirectional Error Meter (Canvas-based)
        # Shows positive/negative error growing from center
        self.bar_error_canvas = tk.Canvas(frame, width=160, height=12,
                                           bg="#e0e0e0", bd=0, highlightthickness=0)
        self.bar_error_canvas.pack(fill=tk.X, pady=(0, 5))
        # Center line marker
        self.bar_error_canvas.create_line(80, 0, 80, 12, fill="gray")
        # Dynamic error bar (starts at center)
        self.bar_error_rect = self.bar_error_canvas.create_rectangle(80, 2, 80, 10, fill="green")

        # Integrator
        int_frame = ttk.Frame(frame)
        int_frame.pack(fill=tk.X)
        ttk.Label(int_frame, text="∫ Err:", width=8).pack(side=tk.LEFT)
        self.lbl_errorI = ttk.Label(int_frame, text="0.0",
                                     font=("Courier", 12), foreground="orange", width=8)
        self.lbl_errorI.pack(side=tk.LEFT)

        # PID Output
        out_frame = ttk.Frame(frame)
        out_frame.pack(fill=tk.X)
        ttk.Label(out_frame, text="PID Out:", width=8).pack(side=tk.LEFT)
        self.lbl_output = ttk.Label(out_frame, text="0.0",
                                     font=("Courier", 12), foreground="purple", width=8)
        self.lbl_output.pack(side=tk.LEFT)

        # VFD % (calculated) and estimated Hz
        vfd_frame = ttk.Frame(frame)
        vfd_frame.pack(fill=tk.X)
        ttk.Label(vfd_frame, text="VFD %:", width=8).pack(side=tk.LEFT)
        self.lbl_vfd_pct = ttk.Label(vfd_frame, text="0%",
                                      font=("Courier", 12), foreground="brown", width=5)
        self.lbl_vfd_pct.pack(side=tk.LEFT)
        # Estimated Hz for VFD verification
        self.lbl_hz = ttk.Label(vfd_frame, text="(0Hz)",
                                 font=("Arial", 9), foreground="gray")
        self.lbl_hz.pack(side=tk.LEFT, padx=(2, 0))

        # Revs counter (for threading, §10.2)
        revs_frame = ttk.Frame(frame)
        revs_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(revs_frame, text="Revs:", width=8).pack(side=tk.LEFT)
        self.lbl_revs = ttk.Label(revs_frame, text="0.00",
                                   font=("Courier", 12), foreground="teal", width=8)
        self.lbl_revs.pack(side=tk.LEFT)
    
    def _setup_status(self, parent: ttk.Frame):
        """Setup status indicator LEDs."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 5))

        self.status_indicators = {}
        indicators = [
            ('at_speed', 'AT SPEED'),
            ('watchdog', 'WATCHDOG'),
            ('spindle_on', 'ENABLED'),
            ('encoder_ok', 'ENCODER'),
            ('safety_chain', 'EXTERNAL'),
        ]

        for key, text in indicators:
            lbl = ttk.Label(frame, text=text, padding=(4, 0))
            lbl.pack(side=tk.LEFT, padx=2)
            self.status_indicators[key] = lbl

    def _set_status_led(self, key: str, ok: bool, warn: bool = False):
        lbl = self.status_indicators.get(key)
        if not lbl:
            return
        if ok:
            color = "green" if not warn else "orange"
        else:
            color = "red"
        lbl.config(foreground=color)
    
    def _setup_statistics(self, parent: ttk.Frame):
        """Setup statistics panel showing min/max/avg."""
        stats_frame = ttk.LabelFrame(parent, text=f"Statistics ({STATS_WINDOW_S:.0f}s)", padding="5")
        stats_frame.pack(fill=tk.X, padx=5)
        
        stats = [
            ('error_avg', 'Avg Error:', 'blue'),
            ('error_min', 'Min Error:', 'green'),
            ('error_max', 'Max Error:', 'red'),
            ('error_std', 'Std Dev:', 'purple'),
            ('peak_error', 'Sess Peak:', 'darkred'),  # Persistent peak
            ('stability', 'Stability:', 'black'),
        ]
        
        for key, label, color in stats:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=1)
            
            ttk.Label(frame, text=label, font=("Arial", 9), width=9).pack(side=tk.LEFT)
            lbl = ttk.Label(frame, text="--", font=("Courier", 10), 
                           foreground=color, width=8)
            lbl.pack(side=tk.LEFT)
            self.stats_labels[key] = lbl
        
        # Reset button
        ttk.Button(stats_frame, text="Reset Stats",
                  command=self._reset_statistics).pack(fill=tk.X, pady=(5, 0))
    
    def _setup_quick_controls(self, parent: ttk.Frame):
        """Setup quick speed controls and presets."""
        frame = ttk.LabelFrame(parent, text="Controls", padding=5)
        frame.pack(fill=tk.X, pady=(0, 5))

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, pady=2)
        ttk.Label(top, text="RPM:").pack(side=tk.LEFT)
        # Register validation command to allow only numeric input
        vcmd = (top.register(self._validate_speed_entry), '%P')
        self.speed_entry = ttk.Entry(top, width=6, validate='key',
                                     validatecommand=vcmd)
        self.speed_entry.insert(0, "1000")
        self.speed_entry.pack(side=tk.LEFT, padx=(2, 4))
        self.speed_entry.bind('<Return>', lambda e: self._go_to_speed())
        ttk.Button(top, text="Go", width=4, command=self._go_to_speed).pack(side=tk.LEFT)

        self.btn_stop = tk.Button(
            frame, text="■ STOP (M5)", command=self._stop_spindle,
            bg="#cc0000", fg="white", font=("Arial", 10, "bold")
        )
        self.btn_stop.pack(fill=tk.X, pady=(4, 4))

        presets = ttk.Frame(frame)
        presets.pack(fill=tk.X, pady=2)
        for speed in [500, 1000, 1500, 1800]:
            ttk.Button(presets, text=str(speed), width=5,
                       command=lambda s=speed: self._start_spindle(s)).pack(
                side=tk.LEFT, padx=1)

        dir_row = ttk.Frame(frame)
        dir_row.pack(fill=tk.X, pady=(4, 2))
        ttk.Button(dir_row, text="CW (M3)", width=8,
                   command=lambda: self._start_spindle(direction='cw')).pack(side=tk.LEFT, padx=2)
        ttk.Button(dir_row, text="CCW (M4)", width=8,
                   command=lambda: self._start_spindle(direction='ccw')).pack(side=tk.LEFT, padx=2)

        preset_row = ttk.Frame(frame)
        preset_row.pack(fill=tk.X, pady=(4, 0))
        for name in ["conservative", "baseline", "aggressive"]:
            ttk.Button(preset_row, text=name.title(), width=10,
                       command=lambda p=name: self.apply_preset(p)).pack(side=tk.LEFT, padx=1)
    
    def _setup_plot(self, parent: ttk.Frame):
        """Setup real-time plot with matplotlib and enhanced controls."""
        plot_frame = ttk.LabelFrame(parent, text="Real-Time Plot", padding="5")
        plot_frame.pack(fill=tk.BOTH, expand=True)

        if not HAS_MATPLOTLIB:
            ttk.Label(
                plot_frame,
                text="Matplotlib not available – text telemetry mode",
                font=("Arial", 10, "bold")
            ).pack(pady=(0, 5))

            self.text_fallback = tk.Text(
                plot_frame,
                font=("Courier New", 11),
                state=tk.DISABLED,
                bg="#111111",
                fg="#EEEEEE",
                relief="flat",
                borderwidth=8
            )
            self.text_fallback.pack(fill=tk.BOTH, expand=True)
            return
        
        # Plot controls bar
        controls = ttk.Frame(plot_frame)
        controls.pack(fill=tk.X, pady=(0, 5))
        
        # Pause/Resume button
        self.btn_pause = ttk.Button(controls, text="⏸ Pause", width=10,
                                    command=self._toggle_plot_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        
        # Time scale selector
        ttk.Label(controls, text="Time:").pack(side=tk.LEFT, padx=(10, 2))
        for scale in TIME_SCALE_OPTIONS:
            rb = ttk.Radiobutton(controls, text=f"{scale}s", value=scale,
                                variable=self.time_scale,
                                command=self._on_time_scale_change)
            rb.pack(side=tk.LEFT, padx=2)
        
        # Dual axis toggle
        ttk.Checkbutton(controls, text="Dual Y-axis", variable=self.dual_axis,
                       command=self._setup_plot_axes).pack(side=tk.LEFT, padx=10)
        
        # Grid toggle
        self.plot_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Grid", variable=self.plot_grid,
                       command=self._toggle_plot_grid).pack(side=tk.LEFT, padx=5)

        self.plot_mode_label = ttk.Label(
            controls, text="Plot: Command, Feedback, Error, Integrator", foreground="gray40"
        )
        self.plot_mode_label.pack(side=tk.LEFT, padx=10)

        # Initialize trace visibility variables before building axes so defaults apply
        for name, config in PLOT_TRACES.items():
            if name not in self.show_traces:
                self.show_traces[name] = tk.BooleanVar(value=PLOT_DEFAULTS.get(name, True))

        # Fit button (manual auto-scale without clearing data)
        ttk.Button(controls, text="Fit", width=4,
                  command=self._fit_plot).pack(side=tk.LEFT, padx=5)
        
        # Export data button
        ttk.Button(controls, text="📊 Data", width=7,
                  command=self._export_plot_data).pack(side=tk.RIGHT, padx=2)
        
        # Screenshot button
        ttk.Button(controls, text="📷 Save", width=7,
                  command=self._save_plot).pack(side=tk.RIGHT, padx=2)
        
        # Clear button
        ttk.Button(controls, text="Clear", width=6,
                  command=self._clear_plot).pack(side=tk.RIGHT, padx=2)
        
        # Create figure with tight layout for better use of space
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.set_tight_layout(True)
        self._setup_plot_axes()
        
        # Embed in Tk
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Connect events for blitting optimization
        self.canvas.mpl_connect('draw_event', self._on_plot_draw)
        self.canvas.mpl_connect('resize_event', lambda e: setattr(self, 'plot_dirty', True))
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Trace visibility controls
        trace_frame = ttk.Frame(plot_frame)
        trace_frame.pack(fill=tk.X)

        ttk.Label(trace_frame, text="Show:", font=("Arial", 9)).pack(side=tk.LEFT)
        for name, config in PLOT_TRACES.items():
            var = self.show_traces[name]
            label = config.get('label', name)
            cb = ttk.Checkbutton(trace_frame, text=label,
                                variable=var, command=self._update_trace_visibility)
            cb.pack(side=tk.LEFT, padx=5)
        # Initialize dynamic label to match default visible traces
        self._update_plot_mode_label()
    
    def _setup_plot_axes(self):
        """Setup or reconfigure plot axes."""
        if self.figure is None:
            return

        self.figure.clear()
        self.background = None  # Reset blitting background
        self.plot_dirty = True  # Request full redraw
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("RPM")
        self.ax.set_xlim(0, self.time_scale.get())
        self.ax.set_ylim(-100, 2000)  # Initial range
        # Respect current grid toggle state when rebuilding axes
        grid_enabled = True if not hasattr(self, "plot_grid") else self.plot_grid.get()
        self.ax.grid(grid_enabled, alpha=0.3)

        # Create lines with animated=True for blitting optimization
        self.lines = {}
        animated = not self.dual_axis.get()

        if self.dual_axis.get():
            # Dual axis mode: RPM on left, error on right
            self.ax2 = self.ax.twinx()
            self.ax2.set_ylabel("Error (RPM)", color='red')
            self.ax2.tick_params(axis='y', labelcolor='red')
            
            # RPM traces on primary axis
            for name in ['cmd', 'feedback']:
                if name in PLOT_TRACES:
                    config = PLOT_TRACES[name]
                    color = config.get('color', 'black')
                    label = config.get('label', name)
                    line, = self.ax.plot([], [], color=color,
                                        label=label, linewidth=1.5,
                                        animated=animated)
                    self.lines[name] = line

            # Error traces on secondary axis
            for name in ['error', 'errorI']:
                if name in PLOT_TRACES:
                    config = PLOT_TRACES[name]
                    color = config.get('color', 'black')
                    label = config.get('label', name)
                    line, = self.ax2.plot([], [], color=color,
                                         label=label, linewidth=1.5,
                                         linestyle='--', animated=animated)
                    self.lines[name] = line
        else:
            # Single axis mode
            self.ax2 = None
            for name, config in PLOT_TRACES.items():
                color = config.get('color', 'black')
                label = config.get('label', name)
                line, = self.ax.plot([], [], color=color,
                                    label=label, linewidth=1.5,
                                    animated=animated)
                self.lines[name] = line

        # Apply existing trace visibility preferences (e.g., after toggling dual axis)
        for name, line in self.lines.items():
            visible_var = self.show_traces.get(name)
            if isinstance(visible_var, tk.BooleanVar):
                line.set_visible(visible_var.get())

        # Build legend using only visible traces to reflect defaults immediately
        if self.dual_axis.get():
            lines1 = [l for l in self.ax.get_lines() if l.get_visible()]
            labels1 = [l.get_label() for l in lines1]
            if self.ax2:
                lines2 = [l for l in self.ax2.get_lines() if l.get_visible()]
                labels2 = [l.get_label() for l in lines2]
                if lines1 or lines2:
                    self.ax.legend(lines1 + lines2, labels1 + labels2,
                                   loc='upper right', fontsize=8, framealpha=0.5)
        else:
            visible_lines = [line for line in self.ax.get_lines() if line.get_visible()]
            if visible_lines:
                self.ax.legend(visible_lines,
                               [line.get_label() for line in visible_lines],
                               loc='upper right', fontsize=8, framealpha=0.5)


        if self.canvas:
            self.canvas.draw()

    def _fit_plot(self):
        """Request a plot rescale and trigger a redraw."""
        self.plot_dirty = True
        if self.canvas:
            self.canvas.draw_idle()

    def _setup_canvas_fallback(self, parent: ttk.Frame):
        """
        Setup enhanced Canvas-based fallback for systems without matplotlib.

        Provides a real-time line chart and telemetry display using pure Tkinter.
        """
        # Main container
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with note
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(header, text="Real-Time Monitor",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text="(matplotlib unavailable)",
                  font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=10)

        # Controls bar
        controls = ttk.Frame(main_frame)
        controls.pack(fill=tk.X, pady=(0, 5))

        self.btn_pause_fallback = ttk.Button(controls, text="⏸ Pause", width=10,
                                              command=self._toggle_plot_pause)
        self.btn_pause_fallback.pack(side=tk.LEFT, padx=2)

        ttk.Button(controls, text="Clear", width=8,
                   command=self._clear_fallback_chart).pack(side=tk.LEFT, padx=2)

        # Trace visibility checkboxes
        trace_frame = ttk.Frame(controls)
        trace_frame.pack(side=tk.LEFT, padx=10)

        self.fallback_traces = {
            'cmd': tk.BooleanVar(value=True),
            'feedback': tk.BooleanVar(value=True),
            'error': tk.BooleanVar(value=True),
        }

        trace_colors = {'cmd': 'blue', 'feedback': 'green', 'error': 'red'}
        trace_labels = {'cmd': 'Cmd', 'feedback': 'Actual', 'error': 'Error'}

        for name, var in self.fallback_traces.items():
            cb = ttk.Checkbutton(trace_frame, text=trace_labels[name],
                                  variable=var)
            cb.pack(side=tk.LEFT, padx=3)

        # Chart canvas
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        # Chart dimensions
        self.chart_width = 500
        self.chart_height = 200
        self.chart_margin = {'left': 50, 'right': 20, 'top': 10, 'bottom': 25}

        self.fallback_chart = tk.Canvas(chart_frame, bg="white",
                                         highlightthickness=1, highlightbackground="#ccc")
        self.fallback_chart.pack(fill=tk.BOTH, expand=True, pady=5)

        # Bind resize event
        self.fallback_chart.bind("<Configure>", self._on_fallback_chart_resize)

        # Draw initial grid and axes
        self._draw_fallback_grid()

        # Legend
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill=tk.X, pady=2)

        for name, color in trace_colors.items():
            lf = ttk.Frame(legend_frame)
            lf.pack(side=tk.LEFT, padx=10)
            legend_canvas = tk.Canvas(lf, width=20, height=10, highlightthickness=0)
            legend_canvas.pack(side=tk.LEFT, padx=2)
            legend_canvas.create_line(0, 5, 20, 5, fill=color, width=2)
            ttk.Label(lf, text=trace_labels[name], font=("Arial", 8)).pack(side=tk.LEFT)

        ttk.Label(
            legend_frame,
            text="Error trace scaled ×5 and centered for visibility",
            font=("Arial", 8),
            foreground="#666",
        ).pack(side=tk.RIGHT, padx=10)

        # Telemetry summary below the chart
        self._setup_fallback_telemetry(main_frame)

    def _on_fallback_chart_resize(self, event):
        """Handle chart canvas resize."""
        self.chart_width = event.width
        self.chart_height = event.height
        self._draw_fallback_grid()

    def _draw_fallback_grid(self):
        """Draw axis grid on the fallback chart canvas."""
        if not self.fallback_chart:
            return

        self.fallback_chart.delete("grid")
        self.fallback_chart.delete("axis")

        w = self.chart_width
        h = self.chart_height
        m = self.chart_margin

        plot_w = w - m['left'] - m['right']
        plot_h = h - m['top'] - m['bottom']

        if plot_w <= 0 or plot_h <= 0:
            return

        # Background
        self.fallback_chart.create_rectangle(m['left'], m['top'],
                                              w - m['right'], h - m['bottom'],
                                              fill="#f8f8f8", outline="#ccc", tags="grid")

        # Horizontal grid lines (RPM scale: 0, 500, 1000, 1500, 2000)
        rpm_values = [0, 500, 1000, 1500, 2000]
        for rpm in rpm_values:
            y = m['top'] + plot_h - (rpm / 2000) * plot_h
            self.fallback_chart.create_line(m['left'], y, w - m['right'], y,
                                             fill="#ddd", tags="grid")
            self.fallback_chart.create_text(m['left'] - 5, y, text=str(rpm),
                                             anchor="e", font=("Arial", 7),
                                             fill="#666", tags="axis")

        # Y-axis label
        self.fallback_chart.create_text(12, h / 2, text="RPM", angle=90,
                                         font=("Arial", 8), fill="#666", tags="axis")

        # Time axis labels (0s to 30s)
        time_values = [0, 10, 20, 30]
        for t in time_values:
            x = m['left'] + (t / 30) * plot_w
            y = h - m['bottom'] + 10
            self.fallback_chart.create_text(x, y, text=f"{t}s",
                                             font=("Arial", 7), fill="#666", tags="axis")

        # X-axis label
        self.fallback_chart.create_text(w / 2, h - 5, text="Time (seconds)",
                                         font=("Arial", 8), fill="#666", tags="axis")

    def _clear_fallback_chart(self):
        """Clear the fallback chart data."""
        self.fallback_chart_data.clear()
        if self.fallback_chart:
            self.fallback_chart.delete("data")

    def _setup_fallback_telemetry(self, parent: ttk.Frame):
        """Setup telemetry summary display below the chart."""
        telem_frame = ttk.LabelFrame(parent, text="Live Telemetry", padding="5")
        telem_frame.pack(fill=tk.X, pady=5)

        # Create a grid layout for metrics
        self.fallback_labels = {}

        metrics = [
            ('cmd', 'Command', 'blue', 'RPM'),
            ('feedback', 'Actual', 'green', 'RPM'),
            ('error', 'Error', 'red', 'RPM'),
            ('errorI', 'Integrator', 'orange', ''),
            ('output', 'PID Output', 'purple', ''),
            ('revs', 'Revolutions', 'teal', 'rev'),
        ]

        # Two rows of three metrics
        row1 = ttk.Frame(telem_frame)
        row1.pack(fill=tk.X, pady=2)
        row2 = ttk.Frame(telem_frame)
        row2.pack(fill=tk.X, pady=2)

        for i, (key, label, color, unit) in enumerate(metrics):
            frame = row1 if i < 3 else row2
            metric_frame = ttk.Frame(frame)
            metric_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

            ttk.Label(metric_frame, text=f"{label}:",
                      font=("Arial", 9)).pack(side=tk.LEFT)

            value_label = ttk.Label(metric_frame, text="0",
                                     font=("Courier", 12, "bold"),
                                     foreground=color, width=8)
            value_label.pack(side=tk.LEFT, padx=2)

            if unit:
                ttk.Label(metric_frame, text=unit,
                          font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)

            self.fallback_labels[key] = value_label

        # Progress bar for command/feedback comparison
        bar_frame = ttk.Frame(telem_frame)
        bar_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(bar_frame, text="RPM:", font=("Arial", 8)).pack(side=tk.LEFT)

        self.fallback_bar_canvas = tk.Canvas(bar_frame, height=20,
                                              highlightthickness=0, bg="#f0f0f0")
        self.fallback_bar_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Bars will be drawn in update

    def _update_canvas_fallback(self, values: Dict[str, float]):
        """Update the Canvas-based fallback display."""
        if not self.fallback_chart:
            return

        # Extract values
        cmd = self._coerce_float(values.get('cmd_limited', 0))
        feedback = self._coerce_float(values.get('feedback', 0))
        error = self._coerce_float(values.get('error', 0))
        errorI = self._coerce_float(values.get('errorI', 0))
        output = self._coerce_float(values.get('output', 0))
        revs = self._coerce_float(values.get('spindle_revs', 0))

        # Update telemetry labels
        if hasattr(self, 'fallback_labels'):
            self.fallback_labels['cmd'].config(text=f"{cmd:.0f}")
            self.fallback_labels['feedback'].config(text=f"{feedback:.0f}")

            # Color-code error based on magnitude
            abs_err = abs(error)
            if abs_err < ERROR_THRESHOLD_EXCELLENT:
                err_color = "green"
            elif abs_err < ERROR_THRESHOLD_GOOD:
                err_color = "blue"
            elif abs_err < ERROR_THRESHOLD_WARNING:
                err_color = "orange"
            else:
                err_color = "red"

            self.fallback_labels['error'].config(text=f"{error:.1f}", foreground=err_color)
            self.fallback_labels['errorI'].config(text=f"{errorI:.1f}")
            self.fallback_labels['output'].config(text=f"{output:.1f}")
            self.fallback_labels['revs'].config(text=f"{revs:.2f}")

    def _update_text_fallback(self, values: Dict[str, float]):
        if self.text_fallback is None or not isinstance(self.text_fallback, tk.Text):
            return

        cmd = values.get('cmd_limited', 0)
        fb = values.get('feedback', 0)
        err = values.get('error', 0)
        errI = values.get('errorI', 0)
        out = values.get('output', 0)
        revs = values.get('spindle_revs', 0)

        self.text_fallback.config(state=tk.NORMAL)
        self.text_fallback.delete('1.0', tk.END)

        text = (
            f"Time: {time.strftime('%H:%M:%S')}\n"
            f"Cmd:       {cmd:8.0f} RPM\n"
            f"Feedback:  {fb:8.0f} RPM\n"
            f"Error:     {err:8.1f} RPM\n"
            f"Integrator: {errI:8.1f}\n"
            f"PID Out:   {out:8.1f}\n"
            f"Revs:      {revs:8.2f}\n"
        )

        self.text_fallback.insert(tk.END, text)
        self.text_fallback.config(state=tk.DISABLED)

        # Update RPM bar visualization
        if hasattr(self, 'fallback_bar_canvas'):
            self._update_fallback_bars(cmd, fb)

        # Add data point to chart history
        self.fallback_chart_data.append({
            'cmd': cmd,
            'feedback': fb,
            'error': err,
            'time': time.time()
        })

        # Redraw chart
        self._draw_fallback_data()

    def _update_fallback_bars(self, cmd: float, feedback: float):
        """Update the RPM comparison bar."""
        canvas = self.fallback_bar_canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()

        if w < 10:
            return

        max_rpm = 2000
        bar_height = 8

        # Command bar (blue)
        cmd_width = max(0, min(w - 10, (cmd / max_rpm) * (w - 10)))
        canvas.create_rectangle(5, 2, 5 + cmd_width, 2 + bar_height,
                                 fill="#4a90d9", outline="")
        canvas.create_text(8, 2 + bar_height / 2, text="Cmd",
                            anchor="w", font=("Arial", 6), fill="white")

        # Feedback bar (green)
        fb_width = max(0, min(w - 10, (feedback / max_rpm) * (w - 10)))
        canvas.create_rectangle(5, 12, 5 + fb_width, 12 + bar_height,
                                 fill="#5cb85c", outline="")
        canvas.create_text(8, 12 + bar_height / 2, text="Act",
                            anchor="w", font=("Arial", 6), fill="white")

    def _draw_fallback_data(self):
        """Draw the data lines on the fallback chart."""
        if not self.fallback_chart or not self.fallback_chart_data:
            return

        self.fallback_chart.delete("data")

        w = self.chart_width
        h = self.chart_height
        m = self.chart_margin

        plot_w = w - m['left'] - m['right']
        plot_h = h - m['top'] - m['bottom']

        if plot_w <= 0 or plot_h <= 0:
            return

        data = list(self.fallback_chart_data)
        if len(data) < 2:
            return

        # Time range (last 30 seconds)
        now = time.time()
        time_window = 30.0

        traces = {
            'cmd': ('blue', self.fallback_traces.get('cmd', tk.BooleanVar(value=True))),
            'feedback': ('green', self.fallback_traces.get('feedback', tk.BooleanVar(value=True))),
            'error': ('red', self.fallback_traces.get('error', tk.BooleanVar(value=True))),
        }

        for trace_name, (color, visible_var) in traces.items():
            if not visible_var.get():
                continue

            points = []
            for point in data:
                age = now - point['time']
                if age > time_window:
                    continue

                x = m['left'] + ((time_window - age) / time_window) * plot_w
                value = point.get(trace_name, 0)

                # Scale: RPM 0-2000 for cmd/feedback, -100 to +100 for error
                if trace_name == 'error':
                    # Scale error to fit in chart (center at 1000 RPM equivalent)
                    y_val = 1000 + value * 5  # Scale error by 5x for visibility
                    y_val = max(0, min(2000, y_val))
                else:
                    y_val = max(0, min(2000, value))

                y = m['top'] + plot_h - (y_val / 2000) * plot_h
                points.append((x, y))

            if len(points) >= 2:
                # Draw polyline
                flat_points = [coord for point in points for coord in point]
                self.fallback_chart.create_line(*flat_points, fill=color,
                                                 width=2, tags="data", smooth=True)

    def _setup_parameters(self, parent: ttk.Frame):
        """Setup parameter tuning controls with groups."""
        param_frame = ttk.LabelFrame(parent, text="Parameters", padding="5")
        param_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Control buttons at top
        btn_frame = ttk.Frame(param_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Lock button to prevent accidental changes during tests
        self.lock_btn = ttk.Checkbutton(btn_frame, text="🔓", width=3,
                                         variable=self.params_locked,
                                         command=self._toggle_params_lock)
        self.lock_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Read HAL", width=8,
                  command=self.read_from_hal).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Baseline", width=8,
                  command=self.reset_to_baseline).pack(side=tk.LEFT, padx=2)
        
        # Live apply checkbox
        ttk.Checkbutton(btn_frame, text="Live", variable=self.live_apply,
                       ).pack(side=tk.RIGHT, padx=2)
        
        # Create scrollable frame
        canvas = tk.Canvas(param_frame, width=220)
        scrollbar = ttk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", 
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Group parameters
        param_groups = {
            'PID': ['P', 'I', 'D'],
            'Feedforward': ['FF0', 'FF1'],
            'Limits': ['Deadband', 'MaxErrorI', 'MaxCmdD', 'RateLimit', 'FilterGain'],
        }
        
        for group_name, params in param_groups.items():
            group_frame = ttk.LabelFrame(scrollable, text=group_name, padding="3")
            group_frame.pack(fill=tk.X, pady=3, padx=2)

            for param_name in params:
                if param_name not in TUNING_PARAMS:
                    continue

                pin, desc, min_val, max_val, step, _, _ = self._get_param_meta(param_name)
                
                frame = ttk.Frame(group_frame)
                frame.pack(fill=tk.X, pady=2)
                
                # Label with tooltip and right-click context menu
                lbl = ttk.Label(frame, text=param_name, width=9)
                lbl.pack(side=tk.LEFT)
                Tooltip(lbl, f"{desc}\nRange: {min_val} - {max_val}\nRight-click to reset")
                lbl.bind("<Button-3>", lambda e, p=param_name: self._show_param_context_menu(e, p))
                
                # Variable
                var = tk.DoubleVar(value=BASELINE_PARAMS.get(param_name, 0))
                self.param_vars[param_name] = var
                
                # Scale with right-click context menu
                scale = ttk.Scale(frame, from_=min_val, to=max_val, variable=var,
                                 orient=tk.HORIZONTAL, length=90,
                                 command=lambda v, p=param_name: self._on_slider_change(p, v))
                scale.pack(side=tk.LEFT, padx=2)
                scale.bind("<Button-3>", lambda e, p=param_name: self._show_param_context_menu(e, p))
                self.param_scales[param_name] = scale  # Store for lock control
                
                # Value label - clickable for precision editing
                val_lbl = ttk.Label(frame, text=f"{var.get():.2f}", width=6,
                                    font=("Courier", 9, "underline"),
                                    foreground="blue", cursor="hand2")
                val_lbl.pack(side=tk.LEFT)
                val_lbl.bind("<Button-1>", lambda e, p=param_name: self._edit_param_value(p))
                val_lbl.bind("<Button-3>", lambda e, p=param_name: self._show_param_context_menu(e, p))
                self.param_labels[param_name] = val_lbl
                self._update_param_label_style(param_name)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Apply button at bottom (disabled when live_apply is on)
        self.apply_all_btn = ttk.Button(param_frame, text="Apply All to HAL",
                                         command=self._apply_all_with_feedback)
        self.apply_all_btn.pack(fill=tk.X, pady=5)
        
        # Update button state when live_apply changes
        self.live_apply.trace_add("write", self._update_apply_button_state)
        self._update_apply_button_state()  # Set initial state

    def _update_param_label_style(self, param_name: str):
        baseline = BASELINE_PARAMS.get(param_name)
        if baseline is None:
            return
        current = self.param_vars.get(param_name)
        lbl = self.param_labels.get(param_name)
        if not current or not lbl:
            return

        value = current.get()
        if abs(value - baseline) < 1e-6:
            lbl.config(foreground="gray25", font=("Courier", 9, "underline"))
        else:
            lbl.config(foreground="blue", font=("Courier", 9, "bold", "underline"))
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Bind to parent's top-level window
        root = self.parent.winfo_toplevel()
        
        root.bind('<space>', lambda e: self._handle_hotkey(self._stop_spindle), add="+")
        root.bind('<F5>', lambda e: self._handle_hotkey(self._quick_step_test), add="+")
        root.bind('<Escape>', lambda e: self._handle_hotkey(self._stop_spindle), add="+")

        # Number keys for speed presets
        root.bind('<KeyPress-1>', lambda e: self._handle_hotkey(lambda: self._start_spindle(500)), add="+")
        root.bind('<KeyPress-2>', lambda e: self._handle_hotkey(lambda: self._start_spindle(1000)), add="+")
        root.bind('<KeyPress-3>', lambda e: self._handle_hotkey(lambda: self._start_spindle(1500)), add="+")
        root.bind('<KeyPress-4>', lambda e: self._handle_hotkey(lambda: self._start_spindle(1800)), add="+")

    def _handle_hotkey(self, func):
        """Run a hotkey handler unless focus is on a text entry."""
        focused = self.parent.winfo_toplevel().focus_get()
        if isinstance(focused, (tk.Entry, tk.Text, ttk.Entry)):
            return "break"

        func()
        return "break"
    
    # =========================================================================
    # PARAMETER EDITING
    # =========================================================================
    
    def _edit_param_value(self, param_name: str):
        """Open dialog to edit parameter value with precision."""
        if self.params_locked.get():
            return
        current_val = self.param_vars[param_name].get()
        _, desc, min_val, max_val, _, _, _ = self._get_param_meta(param_name)
        
        new_val = simpledialog.askfloat(
            "Set Parameter", 
            f"Enter new value for {param_name}:\n({desc})\nRange: {min_val} - {max_val}",
            initialvalue=current_val,
            minvalue=min_val,
            maxvalue=max_val,
            parent=self.parent
        )
        
        if new_val is not None:
            # Snap to step (matches HAL behavior)
            new_val = self._snap_param(param_name, new_val)

            # Update UI and HAL
            self.param_vars[param_name].set(new_val)
            self._on_slider_change(param_name, str(new_val))
            self._update_param_label_style(param_name)
    
    def _show_param_context_menu(self, event, param_name: str):
        """Show context menu for parameter with reset option."""
        menu = tk.Menu(self.parent, tearoff=0)
        baseline = BASELINE_PARAMS.get(param_name, 0.0)
        current = self.param_vars[param_name].get()
        
        menu.add_command(
            label=f"Reset to Baseline ({baseline:.2f})", 
            command=lambda: self._reset_single_param(param_name)
        )
        menu.add_separator()
        menu.add_command(
            label="Edit Value...",
            command=lambda: self._edit_param_value(param_name)
        )
        menu.add_separator()
        menu.add_command(label=f"Current: {current:.3f}", state=tk.DISABLED)
        
        menu.post(event.x_root, event.y_root)
    
    def _reset_single_param(self, param_name: str):
        """Reset a single parameter to its baseline value."""
        baseline = BASELINE_PARAMS.get(param_name, 0.0)
        self.param_vars[param_name].set(baseline)
        self._on_slider_change(param_name, str(baseline))
        self._show_status_message(f"Reset {param_name} to baseline ({baseline:.2f})")
    
    def _update_apply_button_state(self, *args):
        """Update Apply button state based on live_apply setting."""
        if hasattr(self, 'apply_all_btn'):
            if self.live_apply.get():
                self.apply_all_btn.config(state=tk.DISABLED)
            else:
                self.apply_all_btn.config(state=tk.NORMAL)
    
    def _toggle_params_lock(self):
        """Toggle parameter lock state to prevent accidental changes."""
        locked = self.params_locked.get()
        new_state = tk.DISABLED if locked else tk.NORMAL

        for scale in self.param_scales.values():
            scale.configure(state=new_state)

        for lbl in self.param_labels.values():
            lbl.configure(state=new_state)

        if hasattr(self, 'lock_btn'):
            self.lock_btn.config(text="🔒" if locked else "🔓")

        self._show_status_message("Parameters locked" if locked else "Parameters unlocked")
    
    def _apply_all_with_feedback(self):
        """Apply all parameters and show feedback."""
        self.apply_all_params()
        self._show_status_message("All parameters applied to HAL")
    
    def _show_status_message(self, message: str, duration_ms: int = 3000):
        """Show temporary status message that auto-clears."""
        if self.status_message:
            self.status_message.config(text=message)
            # Auto-clear after duration
            self.parent.after(duration_ms, lambda: self.status_message.config(text=""))
    
    # =========================================================================
    # SPINDLE CONTROL
    # =========================================================================
    
    def _start_spindle(self, speed: int = None, direction: str = 'cw'):
        """Start spindle at specified speed."""
        if speed is None:
            try:
                speed = int(self.speed_entry.get())
            except ValueError:
                speed = 1000
        
        m_code = 'M3' if direction == 'cw' else 'M4'
        self.hal.send_mdi(f"{m_code} S{speed}")
    
    def _stop_spindle(self):
        """Stop spindle."""
        self.hal.send_mdi("M5")

    def _validate_speed_entry(self, proposed: str) -> bool:
        """Validate speed entry to allow only positive integers.

        Args:
            proposed: The proposed new value after the edit.

        Returns:
            True to accept the input, False to reject it.
        """
        if proposed == "":
            return True  # Allow empty for deletion
        return proposed.isdigit()

    def _go_to_speed(self):
        """Go to speed from entry field."""
        try:
            speed = int(self.speed_entry.get())
            self._start_spindle(speed)
        except ValueError:
            pass
        # Return focus to parent so global hotkeys (Space=Stop) work
        self.parent.focus_set()
    
    def _quick_step_test(self):
        """Quick step test: 500->1200 RPM."""
        self.hal.send_mdi("M3 S500")
        self.parent.after(3000, lambda: self.hal.send_mdi("M3 S1200"))
    
    # =========================================================================
    # PLOT CONTROLS
    # =========================================================================
    
    def _toggle_plot_pause(self):
        """Toggle plot pause state."""
        self.plot_paused = not self.plot_paused
        btn_text = "▶ Resume" if self.plot_paused else "⏸ Pause"

        # Update matplotlib button if it exists
        if hasattr(self, 'btn_pause') and self.btn_pause:
            self.btn_pause.config(text=btn_text)

        # Update fallback button if it exists
        if hasattr(self, 'btn_pause_fallback') and self.btn_pause_fallback:
            self.btn_pause_fallback.config(text=btn_text)
    
    def _on_time_scale_change(self):
        """Handle time scale change."""
        if self.ax:
            scale = self.time_scale.get()
            self.ax.set_xlim(0, scale)
            self.plot_dirty = True
            if self.canvas:
                self.canvas.draw_idle()
    
    def _clear_plot(self):
        """Clear plot data and reset blitting."""
        self.logger.clear_buffers()
        for line in self.lines.values():
            line.set_data([], [])
        self.background = None  # Reset blitting background
        self.plot_dirty = True
        if self.canvas:
            self.canvas.draw_idle()
    
    def _save_plot(self):
        """Save plot as image."""
        if not self.figure:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), 
                      ("SVG files", "*.svg"), ("All files", "*.*")],
            initialfile=f"spindle_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if filepath:
            try:
                self.figure.savefig(filepath, dpi=150, bbox_inches='tight')
                messagebox.showinfo("Saved", f"Plot saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save plot:\n{e}")
    
    def _toggle_plot_grid(self):
        """Toggle plot grid visibility."""
        if self.ax:
            self.ax.grid(self.plot_grid.get(), alpha=0.3)
            self.plot_dirty = True
            if self.canvas:
                self.canvas.draw_idle()
    
    def _export_plot_data(self):
        """Export current plot data to CSV file."""
        if not HAS_MATPLOTLIB or not self.lines:
            messagebox.showinfo("No Data", "No plot data to export.")
            return
        
        # Get times from any line
        times = None
        for line in self.lines.values():
            xdata = line.get_xdata()
            if len(xdata) > 0:
                times = list(xdata)
                break
        
        if not times:
            messagebox.showinfo("No Data", "No plot data to export.")
            return
        
        # Build headers and data columns
        headers = ["Time (s)"]
        columns = [times]
        
        for name, line in self.lines.items():
            if line.get_visible():
                headers.append(PLOT_TRACES.get(name, {}).get('label', name))
                ydata = list(line.get_ydata())
                # Pad with empty if different length
                while len(ydata) < len(times):
                    ydata.append("")
                columns.append(ydata)
        
        # Prompt for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"spindle_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    # Transpose columns to rows
                    for i in range(len(times)):
                        row = [col[i] if i < len(col) else "" for col in columns]
                        writer.writerow(row)
                self._show_status_message(f"Data exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export data:\n{e}")
    
    def _update_trace_visibility(self):
        """Update which traces are visible on plot."""
        for name, line in self.lines.items():
            if name not in self.show_traces:
                # Ensure dynamically created traces have a visibility variable
                self.show_traces[name] = tk.BooleanVar(value=True)

            visible = self.show_traces[name].get()
            line.set_visible(visible)
        # Update the plot mode label to reflect visible traces
        self._update_plot_mode_label()
        # Full redraw needed to update legend/autoscale
        self.plot_dirty = True
        if self.canvas:
            self.canvas.draw_idle()

    def _update_plot_mode_label(self):
        """Update plot mode label to show only visible trace names."""
        visible_labels = []
        for name, config in PLOT_TRACES.items():
            if name in self.show_traces and self.show_traces[name].get():
                visible_labels.append(config.get('label', name))
        if visible_labels:
            label_text = f"Plot: {', '.join(visible_labels)}"
        else:
            label_text = "Plot: (none)"
        if hasattr(self, 'plot_mode_label') and self.plot_mode_label:
            self.plot_mode_label.config(text=label_text)
    
    def _on_plot_draw(self, event):
        """Callback to capture static background for blitting optimization."""
        if event is not None and self.ax is not None:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
    
    # =========================================================================
    # PARAMETER CONTROLS
    # =========================================================================
    
    def _snap_param(self, param_name: str, value: float) -> float:
        """Snap parameter value to configured step (matches HAL's _clamp_and_snap)."""
        _, _, min_val, max_val, step, _, _ = self._get_param_meta(param_name)
        v = max(min_val, min(max_val, value))
        if step and step > 0:
            steps = round((v - min_val) / step)
            v = min_val + steps * step
            v = max(min_val, min(max_val, v))
        return v

    def _on_slider_change(self, param_name: str, value: str):
        """Handle slider change."""
        if self.params_locked.get():
            return
        try:
            val = self._snap_param(param_name, float(value))
            self.param_vars[param_name].set(val)
            if param_name in self.param_labels:
                self.param_labels[param_name].config(text=f"{val:.2f}")
                self._update_param_label_style(param_name)
            
            # Live apply if enabled (dashboard has direct HAL access)
            if self.live_apply.get():
                self.hal.set_param(param_name, val)
            
            # Notify callback only when NOT live applying (avoids double writes)
            elif self.on_param_change:
                self.on_param_change(param_name, val)
        except ValueError:
            pass
    
    def read_from_hal(self):
        """Read current parameter values from HAL."""
        for param_name in self.param_vars:
            value = self._coerce_float(self.hal.get_param(param_name))
            self.param_vars[param_name].set(value)
            if param_name in self.param_labels:
                self.param_labels[param_name].config(text=f"{value:.2f}")
                self._update_param_label_style(param_name)
        self._show_status_message("Parameters loaded from HAL")
    
    def reset_to_baseline(self):
        """Reset all parameters to baseline values."""
        for param_name, value in BASELINE_PARAMS.items():
            if param_name in self.param_vars:
                self.param_vars[param_name].set(value)
                if param_name in self.param_labels:
                    self.param_labels[param_name].config(text=f"{value:.2f}")
                    self._update_param_label_style(param_name)
                if self.live_apply.get():
                    self.hal.set_param(param_name, value)
        self._show_status_message("Reset all parameters to baseline")
    
    def apply_preset(self, preset_name: str):
        """Apply a tuning preset."""
        if preset_name not in PRESETS:
            return
        
        preset = PRESETS[preset_name]
        for param, value in preset.items():
            if param in self.param_vars:
                self.param_vars[param].set(value)
                if param in self.param_labels:
                    self.param_labels[param].config(text=f"{value:.2f}")
                    self._update_param_label_style(param)
                if self.live_apply.get():
                    self.hal.set_param(param, value)
                elif self.on_param_change:
                    self.on_param_change(param, value)
        self._show_status_message(f"Applied '{preset_name}' preset")
    
    def apply_all_params(self):
        """Apply all current parameter values to HAL."""
        for param, var in self.param_vars.items():
            self.hal.set_param(param, var.get())
    
    def get_param_values(self) -> Dict[str, float]:
        """Get current parameter values."""
        return {param: var.get() for param, var in self.param_vars.items()}
    
    def set_param_values(self, params: Dict[str, float]):
        """Set parameter values from dict."""
        for param, value in params.items():
            if param in self.param_vars:
                self.param_vars[param].set(value)
                if param in self.param_labels:
                    self.param_labels[param].config(text=f"{value:.2f}")
                    self._update_param_label_style(param)
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def _reset_statistics(self):
        """Reset statistics collection."""
        self.error_history.clear()
        self.session_peak_error = 0.0  # Reset session peak
        for lbl in self.stats_labels.values():
            lbl.config(text="--")
    
    def _update_statistics(self, error: float):
        """Update statistics with new error value."""
        self.error_history.append(error)

        # Track session peak (absolute max error since reset)
        self.session_peak_error = max(self.session_peak_error, abs(error))

        # Use whatever samples we have instead of waiting for a minimum window
        errors = list(self.error_history)

        if not errors:
            return

        avg = sum(errors) / len(errors)
        min_err = min(errors)
        max_err = max(errors)

        # Standard deviation (sample variance for small windows)
        variance = 0.0 if len(errors) == 1 else sum((e - avg) ** 2 for e in errors) / (len(errors) - 1)
        std = variance ** 0.5
        
        # Stability assessment
        stability_range = max_err - min_err
        if stability_range < 10:
            stability = "Excellent"
            color = "green"
        elif stability_range < 25:
            stability = "Good"
            color = "blue"
        elif stability_range < 50:
            stability = "Fair"
            color = "orange"
        else:
            stability = "Poor"
            color = "red"
        
        # Update labels
        self.stats_labels['error_avg'].config(text=f"{avg:.1f}")
        self.stats_labels['error_min'].config(text=f"{min_err:.1f}")
        self.stats_labels['error_max'].config(text=f"{max_err:.1f}")
        self.stats_labels['error_std'].config(text=f"{std:.1f}")
        self.stats_labels['peak_error'].config(text=f"{self.session_peak_error:.1f}")
        self.stats_labels['stability'].config(text=stability, foreground=color)
    
    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    
    def update(self, values: Dict[str, float]):
        """
        Update dashboard with new values.
        
        Called by main update loop.
        """
        # Update gauges
        cmd = self._coerce_float(values.get('cmd_limited'))
        fb = self._coerce_float(values.get('feedback'))
        err = self._coerce_float(values.get('error'))
        errI = self._coerce_float(values.get('errorI'))
        output = self._coerce_float(values.get('output'))
        
        self.lbl_cmd.config(text=f"{cmd:.0f}")
        self.lbl_feedback.config(text=f"{fb:.0f}")
        self.lbl_error.config(text=f"{err:.1f}")
        self.lbl_errorI.config(text=f"{errI:.1f}")
        self.lbl_output.config(text=f"{output:.1f}")
        
        # Update Visual RPM Bars for slip monitoring
        if self.bar_cmd:
            self.bar_cmd['value'] = abs(cmd)
        if self.bar_fb:
            self.bar_fb['value'] = abs(fb)
        
        # Update Bidirectional Error Meter
        if self.bar_error_canvas and self.bar_error_rect:
            width = 160
            center = width / 2
            scale = 1.0  # Pixels per RPM error
            max_rpm_visual = 100.0

            # Clamp visualization to canvas size
            bar_len = max(-max_rpm_visual, min(max_rpm_visual, err)) * scale
            
            # Determine color based on error magnitude
            abs_err = abs(err)
            if abs_err < ERROR_THRESHOLD_EXCELLENT:
                fill = "green"
            elif abs_err < ERROR_THRESHOLD_GOOD:
                fill = "#88AA00"  # Yellow-green
            elif abs_err < ERROR_THRESHOLD_WARNING:
                fill = "orange"
            else:
                fill = "red"
            
            # Draw bar from center (positive = right, negative = left)
            if bar_len >= 0:
                self.bar_error_canvas.coords(self.bar_error_rect, center, 2, center + bar_len, 10)
            else:
                self.bar_error_canvas.coords(self.bar_error_rect, center + bar_len, 2, center, 10)
            self.bar_error_canvas.itemconfig(self.bar_error_rect, fill=fill)
        
        # VFD % (assuming 1800 RPM = 100%)
        vfd_pct = abs(cmd) / 1800 * 100 if cmd != 0 else 0
        self.lbl_vfd_pct.config(text=f"{vfd_pct:.0f}%")
        
        # Calculate and display Estimated Hz (for VFD verification)
        if hasattr(self.hal, 'rpm_to_hz'):
            hz = self.hal.rpm_to_hz(abs(cmd))
            self.lbl_hz.config(text=f"({hz:.1f}Hz)")
        else:
            self.lbl_hz.config(text="")
        
        # Revs counter (for threading operations)
        revs = self._coerce_float(values.get('spindle_revs'))
        self.lbl_revs.config(text=f"{revs:.2f}")
        
        # Error color coding
        abs_err = abs(err)
        if abs_err <= ERROR_THRESHOLD_EXCELLENT:
            err_color = "green"
        elif abs_err <= ERROR_THRESHOLD_GOOD:
            err_color = "blue"
        elif abs_err <= ERROR_THRESHOLD_WARNING:
            err_color = "orange"
        else:
            err_color = "red"
        self.lbl_error.config(foreground=err_color)
        
        # Direction indicator (use signed feedback_raw for correct CW/CCW detection)
        fb_raw = self._coerce_float(values.get('feedback_raw', fb), default=fb)
        if abs(fb_raw) < 10:
            self.lbl_direction.config(text="STOP", foreground="gray")
        elif fb_raw > 0:
            self.lbl_direction.config(text="CW →", foreground="green")
        else:
            self.lbl_direction.config(text="← CCW", foreground="blue")
        
        # Update status indicators
        at_speed = values.get('at_speed', 0) > 0.5
        watchdog = values.get('watchdog', 0) > 0.5
        spindle_on = values.get('spindle_on', 0) > 0.5
        encoder_ok = values.get('encoder_fault', 0) < 0.5
        external_ok = values.get('safety_chain', 1.0) > 0.5

        self._set_status_led('at_speed', at_speed)
        self._set_status_led('watchdog', watchdog, warn=True)
        self._set_status_led('spindle_on', spindle_on)
        self._set_status_led('encoder_ok', encoder_ok)
        self._set_status_led('safety_chain', external_ok)

        if hasattr(self, 'lbl_spindle_state'):
            self.lbl_spindle_state.config(
                text="ENABLED" if spindle_on else "DISABLED",
                foreground="green" if spindle_on else "red"
            )
        
        # Update statistics
        self._update_statistics(err)
        
        # Auto-reset statistics when spindle stops
        if self.last_cmd > 10 and cmd < 10:
            self._reset_statistics()
        
        # Store for direction detection
        self.last_feedback = fb
        self.last_cmd = cmd
        
        # Update plot (if not paused)
        if not self.plot_paused:
            if HAS_MATPLOTLIB:
                self._update_plot()
            elif isinstance(self.text_fallback, tk.Text):
                self._update_text_fallback(values)
            else:
                self._update_canvas_fallback(values)
    
    def _update_plot(self):
        """
        Update plot with latest data using blitting for performance.
        
        Blitting optimization significantly reduces CPU usage on Raspberry Pi
        by only redrawing the animated lines, not the entire figure.
        """
        if not HAS_MATPLOTLIB or self.canvas is None:
            return
        
        times, trace_data = self.logger.get_plot_data()

        if times is None or len(times) == 0:
            return
        
        # Update line data
        for name, line in self.lines.items():
            series = trace_data.get(name, [])
            line.set_data(times, series)
        
        # Check if we need a full redraw (axis shift, resize, etc.)
        time_scale = self.time_scale.get()
        current_xlim = self.ax.get_xlim()
        x_max = max(times[-1], time_scale)
        x_min = max(0, x_max - time_scale)
        
        needs_full_redraw = (
            self.plot_dirty or
            self.background is None or
            times[-1] > current_xlim[1]  # X-axis needs to shift
        )
        
        if needs_full_redraw:
            # Full redraw: update axes and redraw everything
            self.ax.set_xlim(x_min, x_max)
            
            # Auto-scale y-axis
            if self.dual_axis.get():
                # Separate scaling for RPM and error axes
                rpm_data = []
                err_data = []
                
                for name in ['cmd', 'feedback']:
                    if name in self.lines and name in self.show_traces and self.show_traces[name].get():
                        data = self.lines[name].get_ydata()
                        if len(data) > 0:
                            rpm_data.extend(data)

                for name in ['error', 'errorI']:
                    if name in self.lines and name in self.show_traces and self.show_traces[name].get():
                        data = self.lines[name].get_ydata()
                        if len(data) > 0:
                            err_data.extend(data)
                
                if rpm_data:
                    y_min = min(rpm_data) - 50
                    y_max = max(rpm_data) + 50
                    self.ax.set_ylim(y_min, y_max)
                
                if err_data and self.ax2:
                    y_min = min(err_data) - 10
                    y_max = max(err_data) + 10
                    self.ax2.set_ylim(y_min, y_max)
            else:
                # Single axis scaling
                all_data = []
                for name, line in self.lines.items():
                    if name in self.show_traces and self.show_traces[name].get():
                        data = line.get_ydata()
                        if len(data) > 0:
                            all_data.extend(data)
                
                if all_data:
                    y_min = min(all_data) - 50
                    y_max = max(all_data) + 50
                    self.ax.set_ylim(y_min, y_max)
            
            # Regenerate legend with only visible traces to fix de-sync issue
            if self.dual_axis.get():
                lines1 = [l for l in self.ax.get_lines() if l.get_visible()]
                labels1 = [l.get_label() for l in lines1]
                if self.ax2:
                    lines2 = [l for l in self.ax2.get_lines() if l.get_visible()]
                    labels2 = [l.get_label() for l in lines2]
                    if lines1 or lines2:
                        self.ax.legend(lines1 + lines2, labels1 + labels2,
                                      loc='upper right', fontsize=8, framealpha=0.5)
            else:
                visible_lines = [(name, line) for name, line in self.lines.items()
                                if line.get_visible()]
                if visible_lines:
                    self.ax.legend([l for _, l in visible_lines],
                                  [PLOT_TRACES.get(n, {}).get('label', n) for n, _ in visible_lines],
                                  loc='upper right', fontsize=8, framealpha=0.5)
                elif self.ax.get_legend():
                    self.ax.get_legend().remove()

            # Expensive full redraw
            self.canvas.draw()
            self.plot_dirty = False
            # Background will be recaptured by _on_plot_draw callback
        else:
            # Blitting with dual axes can produce artifacts; fall back to full draw
            if self.dual_axis.get():
                self.canvas.draw()
                return

            # Fast blitting update: restore background, draw lines, blit
            if self.background is not None:
                self.canvas.restore_region(self.background)

                # Draw only visible animated lines on correct axis
                for name, line in self.lines.items():
                    if line.get_visible():
                        if self.dual_axis.get() and name in ['error', 'errorI'] and self.ax2:
                            self.ax2.draw_artist(line)
                        else:
                            self.ax.draw_artist(line)

                self.canvas.blit(self.ax.bbox)
                self.canvas.flush_events()
    
