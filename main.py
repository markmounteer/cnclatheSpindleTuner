#!/usr/bin/env python3
"""
Spindle Tuner v6.0 - Application Entry Point

A comprehensive spindle PID tuning companion for LinuxCNC.
Based on the Spindle PID Tuning Guide v5.3 for Grizzly 7x14 lathe.

Usage:
    python main.py [--mock]
    
Options:
    --mock    Run in mock mode (no HAL connection required)
"""

import sys
import time
import logging
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_TITLE, APP_VERSION, UPDATE_INTERVAL_MS
from hal_interface import HalInterface, IniFileHandler, ConnectionState
from logger import DataLogger
from dashboard import DashboardTab
from tests import TestsTab, ChecklistsTab  # Now imports from tests/ package
from troubleshooter import TroubleshooterTab
from export import ExportTab

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Main")


class SpindleTunerApp:
    """
    Main application class.
    
    Wires together all feature slices and manages the update loop.
    """
    
    def __init__(self, root: tk.Tk, mock: bool = False):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
            mock: Whether to run in mock mode
        """
        self.root = root
        self.root.title(APP_TITLE + (" [MOCK MODE]" if mock else ""))
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)  # Prevent UI breaking at small sizes
        
        # Initialize core services
        logger.info("Initializing core services...")
        self.hal = HalInterface(mock=mock)
        self.logger = DataLogger()
        self.ini_handler = IniFileHandler()

        # Current values cache
        self.current_values = {}
        self._last_commanded_speed = None
        self._last_commanded_direction = None
        self._hal_queue: "queue.Queue[dict]" = queue.Queue(maxsize=1)
        self._hal_stop_event = threading.Event()
        self._last_reconnect_attempt = 0.0
        self._reconnect_backoff_s = 5.0
        
        # Store default background for fault status
        self.default_bg = self.root.cget('bg')
        
        # Build UI
        self._setup_menu()
        self._setup_main_layout()
        self._setup_status_bar()
        self._bind_shortcuts()
        
        # Start update loop
        self._last_update_time = time.time()
        self._update_count = 0
        self._start_update_loop()
        
        logger.info("Application started successfully")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session",
                             command=self._new_session, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Load Profile...", 
                             command=self._load_profile, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Profile...", 
                             command=self._save_profile, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export CSV...", 
                             command=self._export_csv, accelerator="Ctrl+E")
        file_menu.add_command(label="Generate INI Section...", 
                             command=self._show_ini)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator="Ctrl+Q")
        
        # Spindle menu
        spindle_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Spindle", menu=spindle_menu)
        spindle_menu.add_command(label="Start (M3 S1000)", 
                                command=lambda: self.hal.send_mdi("M3 S1000"))
        spindle_menu.add_command(label="Stop (M5)", 
                                command=lambda: self.hal.send_mdi("M5"))
        spindle_menu.add_separator()
        spindle_menu.add_command(label="Emergency Stop", 
                                command=self._emergency_stop, accelerator="Escape")
        
        # Presets menu
        presets_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Presets", menu=presets_menu)
        presets_menu.add_command(label="Conservative", 
                                command=lambda: self.dashboard.apply_preset('conservative'))
        presets_menu.add_command(label="Baseline (v5.3)", 
                                command=lambda: self.dashboard.apply_preset('baseline'))
        presets_menu.add_command(label="Aggressive", 
                                command=lambda: self.dashboard.apply_preset('aggressive'))
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", 
                             command=lambda: self._select_tab(0), accelerator="Ctrl+1")
        view_menu.add_command(label="Tests", 
                             command=lambda: self._select_tab(1), accelerator="Ctrl+2")
        view_menu.add_command(label="Checklists", 
                             command=lambda: self._select_tab(2), accelerator="Ctrl+3")
        view_menu.add_command(label="Troubleshooter", 
                             command=lambda: self._select_tab(3), accelerator="Ctrl+4")
        view_menu.add_command(label="Export", 
                             command=lambda: self._select_tab(4), accelerator="Ctrl+5")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="HAL Diagnostics...", 
                             command=self._show_hal_diagnostics)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
    
    def _setup_main_layout(self):
        """Setup main application layout with notebook tabs."""
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Dashboard
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        self.dashboard = DashboardTab(
            dashboard_frame, 
            self.hal, 
            self.logger,
            on_param_change=self._on_param_change
        )
        
        # Tab 2: Tests
        tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(tests_frame, text="Tests")
        self.tests = TestsTab(tests_frame, self.hal, self.logger)
        
        # Tab 3: Checklists
        checklist_frame = ttk.Frame(self.notebook)
        self.notebook.add(checklist_frame, text="Checklists")
        self.checklists = ChecklistsTab(checklist_frame)
        
        # Tab 4: Troubleshooter
        troubleshooter_frame = ttk.Frame(self.notebook)
        self.notebook.add(troubleshooter_frame, text="Troubleshooter")
        self.troubleshooter = TroubleshooterTab(troubleshooter_frame, self.hal)
        
        # Tab 5: Export
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export")
        self.export = ExportTab(
            export_frame,
            self.logger,
            self.ini_handler,
            get_params_callback=self.dashboard.get_param_values,
            set_params_callback=self.dashboard.set_param_values
        )
    
    def _setup_status_bar(self):
        """Setup status bar at bottom."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Connection status (dynamic based on HAL state)
        self.status_conn = ttk.Label(self.status_bar, text="Initializing...",
                                     foreground="gray", width=15)
        self.status_conn.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Fault/System Status (uses tk.Label for bg color support)
        self.status_fault = tk.Label(self.status_bar, text="System OK",
                                     font=("Arial", 9, "bold"),
                                     bg=self.default_bg, fg="green", width=25)
        self.status_fault.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Update rate
        self.status_rate = ttk.Label(self.status_bar, text="0 Hz")
        self.status_rate.pack(side=tk.LEFT, padx=5)
        
        # Timestamp
        self.status_time = ttk.Label(self.status_bar, text="")
        self.status_time.pack(side=tk.RIGHT, padx=10)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # File operations (both cases for Caps Lock compatibility)
        self.root.bind('<Control-n>', lambda e: self._new_session())
        self.root.bind('<Control-N>', lambda e: self._new_session())
        self.root.bind('<Control-o>', lambda e: self._load_profile())
        self.root.bind('<Control-O>', lambda e: self._load_profile())
        self.root.bind('<Control-s>', lambda e: self._save_profile())
        self.root.bind('<Control-S>', lambda e: self._save_profile())
        self.root.bind('<Control-e>', lambda e: self._export_csv())
        self.root.bind('<Control-E>', lambda e: self._export_csv())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Control-Q>', lambda e: self._on_closing())
        
        # Spindle control
        self.root.bind('<F5>', lambda e: self.tests.run_step_test())
        self.root.bind('<F8>', lambda e: self.tests.run_full_suite())
        self.root.bind('<space>', lambda e: self._toggle_spindle())
        self.root.bind('<Escape>', lambda e: self._emergency_stop())
        
        # Tab navigation (Ctrl+1 through Ctrl+5)
        for i in range(5):
            self.root.bind(f'<Control-Key-{i+1}>', 
                          lambda e, idx=i: self._select_tab(idx))
        
        # Tab navigation (Ctrl+Page Up/Down)
        self.root.bind('<Control-Prior>', lambda e: self._prev_tab())
        self.root.bind('<Control-Next>', lambda e: self._next_tab())
    
    def _select_tab(self, index: int):
        """Select a notebook tab by index."""
        if 0 <= index < self.notebook.index('end'):
            self.notebook.select(index)
    
    def _prev_tab(self):
        """Navigate to previous tab."""
        current = self.notebook.index(self.notebook.select())
        total = self.notebook.index("end")
        self.notebook.select((current - 1) % total)
    
    def _next_tab(self):
        """Navigate to next tab."""
        current = self.notebook.index(self.notebook.select())
        total = self.notebook.index("end")
        self.notebook.select((current + 1) % total)
    
    def _start_update_loop(self):
        """Start the main update loop."""
        self._start_hal_worker()
        self._update()

    def _update(self):
        """Main update loop - called every UPDATE_INTERVAL_MS."""
        start_time = time.time()
        try:
            # 1. Update Connection Status
            self._update_connection_status()

            # 2. Get current values from HAL
            try:
                self.current_values = self._hal_queue.get_nowait()
            except queue.Empty:
                pass

            self._track_last_spindle_command()
            
            # 3. Check for Faults/E-Stop
            self._update_fault_status()
            
            # 4. Add to data logger
            self.logger.add_sample(self.current_values)
            
            # 5. Update UI components
            self.dashboard.update(self.current_values)
            
            # Update tests tab (revs display)
            revs = self.current_values.get('spindle_revs', 0)
            self.tests.update_revs(revs)
            
            # Update export tab points display
            self.export.update_points_display()
            
            # 6. Update general status bar info (rate, time)
            self._update_status_bar_metrics()
            
        except Exception as e:
            logger.error(f"Update loop error: {e}")

        # Schedule next update
        elapsed = (time.time() - start_time) * 1000
        next_delay = max(1, int(UPDATE_INTERVAL_MS - elapsed))
        self.root.after(next_delay, self._update)

    def _start_hal_worker(self):
        """Start background worker to fetch HAL values."""
        def worker():
            while not self._hal_stop_event.is_set():
                loop_start = time.time()
                try:
                    values = self.hal.get_all_values()
                    try:
                        self._hal_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._hal_queue.put(values)
                except Exception as e:
                    logger.error(f"HAL fetch error: {e}")

                elapsed = time.time() - loop_start
                sleep_time = max(0, (UPDATE_INTERVAL_MS / 1000.0) - elapsed)
                self._hal_stop_event.wait(sleep_time)

        threading.Thread(target=worker, daemon=True).start()

    def _track_last_spindle_command(self):
        """Track the most recent commanded spindle speed and direction."""
        cmd_raw = self.current_values.get('cmd_raw')
        if cmd_raw is None:
            cmd_raw = self.current_values.get('cmd_limited')

        if cmd_raw is None:
            return

        speed = abs(cmd_raw)
        if speed <= 0:
            return

        direction = 'M3' if cmd_raw > 0 else 'M4'
        self._last_commanded_speed = speed
        self._last_commanded_direction = direction
    
    def _update_connection_status(self):
        """Update connection indicator based on HAL state."""
        state = self.hal.connection_state
        
        if state == ConnectionState.MOCK:
            self.status_conn.config(text="● MOCK MODE", foreground="orange")
        elif state == ConnectionState.CONNECTED:
            self.status_conn.config(text="● Connected", foreground="green")
        elif state == ConnectionState.CONNECTING:
            self.status_conn.config(text="◌ Connecting...", foreground="blue")
        else:  # DISCONNECTED or ERROR
            self.status_conn.config(text="● Disconnected", foreground="red")
            now = time.monotonic()
            if (now - self._last_reconnect_attempt) >= self._reconnect_backoff_s:
                self._last_reconnect_attempt = now
                self.hal.reconnect()
    
    def _update_fault_status(self):
        """Monitor safety signals and update fault display."""
        faults = []
        
        # Check encoder fault
        if self.current_values.get('encoder_fault', 0) > 0.5:
            faults.append("ENCODER FAULT")
        
        # Check external OK (Safety Chain) - 1.0 = OK, 0.0 = Fault
        if self.current_values.get('safety_chain', 1.0) < 0.5:
            faults.append("E-STOP ACTIVE")
        
        if faults:
            msg = f"⚠ {' | '.join(faults)}"
            self.status_fault.config(text=msg, bg="red", fg="white")
        else:
            self.status_fault.config(text="System OK", bg=self.default_bg, fg="green")

    def _update_status_bar_metrics(self):
        """Update rate and time in status bar."""
        # Update rate calculation
        self._update_count += 1
        now = time.time()
        elapsed = now - self._last_update_time
        
        if elapsed >= 1.0:
            rate = self._update_count / elapsed
            self.status_rate.config(text=f"{rate:.1f} Hz")
            self._update_count = 0
            self._last_update_time = now
        
        # Timestamp
        from datetime import datetime
        self.status_time.config(text=datetime.now().strftime("%H:%M:%S"))
    
    def _on_param_change(self, param: str, value: float):
        """Handle parameter change from dashboard."""
        self.hal.set_param(param, value)
    
    def _toggle_spindle(self):
        """Toggle spindle on/off."""
        focused = self.root.focus_get()
        if isinstance(focused, (tk.Entry, tk.Text, ttk.Entry)):
            return

        if self.current_values.get('spindle_on', 0) > 0.5:
            self.hal.send_mdi("M5")
            logger.info("Spindle stop requested (Spacebar)")
        else:
            if not self._last_commanded_direction or self._last_commanded_speed is None:
                messagebox.showwarning(
                    "Unknown Spindle State",
                    "Cannot resume spindle because the previous direction/speed are unknown."
                    " Please start the spindle manually from the controls."
                )
                logger.warning("Spindle start via toggle blocked: unknown previous state")
                return

            command = f"{self._last_commanded_direction} S{int(round(self._last_commanded_speed))}"
            self.hal.send_mdi(command)
            logger.info("Spindle start requested (Spacebar)")
    
    def _emergency_stop(self):
        """Emergency stop spindle - immediate, no dialogs."""
        logger.warning("EMERGENCY STOP TRIGGERED")
        self.hal.send_mdi("M5")
        if self.hal.is_mock:
            self.hal.set_mock_fault('estop', True)
        self.tests.log_result("*** EMERGENCY STOP ***")
    
    def _new_session(self):
        """Start a new tuning session - clears all recorded data."""
        prompt = (
            "Clear all recorded data and start fresh?\n\n"
            "This will reset the data logger and plot."
        )

        if messagebox.askyesno("New Session", prompt):
            self.logger.clear_buffers()
            self.logger.clear_recording()
            logger.info("New session started - data cleared")
    
    def _on_closing(self):
        """Handle application closure with safety check."""
        try:
            self.hal.send_mdi("M5")
        except Exception:
            logger.warning("Failed to issue spindle stop on exit")

        if self.current_values.get('spindle_on', 0) > 0.5:
            prompt = (
                "The spindle is currently running.\n\n"
                "Yes = Stop spindle and exit\n"
                "No = Exit without stopping\n"
                "Cancel = Don't exit"
            )

            result = messagebox.askyesnocancel("Spindle Running", prompt)
            if result is None:  # Cancel
                return
            elif result:  # Yes - stop spindle first
                self.hal.send_mdi("M5")
                logger.info("Spindle stopped on exit")

        self._hal_stop_event.set()

        logger.info("Application closing...")
        self.root.destroy()
    
    def _load_profile(self):
        """Load profile (delegates to export tab)."""
        self.export.load_profile()
    
    def _save_profile(self):
        """Save profile (delegates to export tab)."""
        self.export.save_profile()
    
    def _export_csv(self):
        """Export CSV (delegates to export tab)."""
        self.export.export_csv()
    
    def _show_ini(self):
        """Show INI config (delegates to export tab)."""
        self.export.show_ini_config()
    
    def _show_hal_diagnostics(self):
        """Show HAL diagnostics dialog."""
        try:
            diagnostics = self.hal.get_diagnostics()
            
            dialog = tk.Toplevel(self.root)
            dialog.title("HAL Diagnostics")
            dialog.geometry("500x350")
            dialog.transient(self.root)
            
            text = tk.Text(dialog, font=("Courier", 10), wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            lines = ["HAL Diagnostics Report", "=" * 40, ""]
            for key, value in diagnostics.items():
                lines.append(f"{key}: {value}")
            
            text.insert(tk.END, "\n".join(lines))
            text.config(state=tk.DISABLED)
            
            ttk.Button(dialog, text="Close", 
                      command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Diagnostics Error", 
                               f"Failed to get diagnostics:\n{e}")
    
    def _show_about(self):
        """Show about dialog with system information."""
        about_text = f"""Spindle Tuner v{APP_VERSION}

A comprehensive spindle PID tuning companion for LinuxCNC.

Features:
• Real-time monitoring with multi-trace plotting
• Automated test procedures (step, decel, load, etc.)
• Pre-flight checks and encoder verification
• Interactive troubleshooter with decision tree
• Hardware and commissioning checklists
• Profile management and INI generation

Based on Spindle PID Tuning Guide v5.3
for Grizzly 7x14 CNC Lathe Conversion.

System Information:
  Python: {sys.version.split()[0]}
  Platform: {sys.platform}
  Mock Mode: {self.hal.is_mock}
  HAL Connected: {self.hal.is_connected}

Keyboard Shortcuts:
  Ctrl+N       - New session
  Ctrl+O       - Load profile
  Ctrl+S       - Save profile
  Ctrl+E       - Export CSV
  Ctrl+Q       - Quit
  Ctrl+1-5     - Switch tabs
  Ctrl+PgUp/Dn - Prev/next tab
  F5           - Run step test
  F8           - Run full test suite
  Space        - Toggle spindle
  Escape       - Emergency stop"""
        
        messagebox.showinfo(f"About Spindle Tuner v{APP_VERSION}", about_text)


def main():
    """Application entry point."""
    # Check for mock mode flag
    mock = '--mock' in sys.argv
    
    # Create root window
    root = tk.Tk()
    
    # Attempt to set a modern theme
    style = ttk.Style()
    available_themes = style.theme_names()
    if 'vista' in available_themes:
        style.theme_use('vista')
    elif 'clam' in available_themes:
        style.theme_use('clam')
    
    # Create application
    app = SpindleTunerApp(root, mock=mock)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app._on_closing)
    
    # Run
    root.mainloop()


if __name__ == "__main__":
    main()
