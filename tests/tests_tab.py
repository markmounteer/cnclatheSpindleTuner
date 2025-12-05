"""
Spindle Tuner - Tests Tab with Tabbed Interface

Provides a tabbed interface where each test has its own tab with:
- Detailed description and purpose
- Step-by-step procedure
- Expected results
- Troubleshooting guidance
- Run button and results display
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import csv
from datetime import datetime
from typing import Optional, Callable, Dict

from config import MONITOR_PINS, BASELINE_PARAMS, MOTOR_SPECS, VFD_SPECS, ENCODER_SPECS

# Import all test classes
from tests.test_signal_chain import SignalChainTest
from tests.test_preflight import PreflightTest
from tests.test_encoder import EncoderTest
from tests.test_open_loop import OpenLoopTest
from tests.test_forward import ForwardTest
from tests.test_reverse import ReverseTest
from tests.test_rate_limit import RateLimitTest
from tests.test_step import StepTest
from tests.test_load import LoadTest
from tests.test_steadystate import SteadyStateTest
from tests.test_decel import DecelTest
from tests.test_ramp import RampTest
from tests.test_full_suite import FullSuiteTest
from tests.test_watchdog import WatchdogTest


class TestsTab:
    """
    Tests feature with tabbed interface.

    Each test is presented on its own tab with:
    - Purpose and description
    - Prerequisites
    - Step-by-step procedure
    - Expected results
    - Troubleshooting tips
    - Run button and configuration options
    """

    # Define test categories and their tests
    TEST_CATEGORIES = [
        ("Pre-Flight", [
            ("Signal Chain", SignalChainTest, "signal_chain"),
            ("Pre-Flight Check", PreflightTest, "preflight"),
            ("Encoder Verification", EncoderTest, "encoder"),
        ]),
        ("Startup", [
            ("Open Loop", OpenLoopTest, "open_loop"),
            ("Forward PID", ForwardTest, "forward"),
            ("Reverse PID", ReverseTest, "reverse"),
            ("Rate Limit", RateLimitTest, "rate_limit"),
        ]),
        ("Performance", [
            ("Step Response", StepTest, "step"),
            ("Load Recovery", LoadTest, "load"),
            ("Steady-State", SteadyStateTest, "steadystate"),
        ]),
        ("Advanced", [
            ("Deceleration", DecelTest, "decel"),
            ("Full Ramp", RampTest, "ramp"),
            ("Full Suite", FullSuiteTest, "full_suite"),
            ("Watchdog (Mock)", WatchdogTest, "watchdog"),
        ]),
    ]

    def __init__(self, parent: ttk.Frame, hal_interface, data_logger,
                 log_callback: Optional[Callable] = None):
        self.parent = parent
        self.hal = hal_interface
        self.logger = data_logger
        self.log_callback = log_callback

        # Test instances
        self.tests: Dict[str, object] = {}

        # UI elements
        self.results_text = None
        self.progress_bar = None
        self.progress_label = None
        self.lbl_revs = None

        # Step test parameters
        self.step_from = None
        self.step_to = None
        self.ss_duration = None

        # Mock controls
        self.load_slider = None
        self.load_label = None
        self.mock_buttons = {}

        self._setup_ui()
        self._create_test_instances()

    def _setup_ui(self):
        """Build the tabbed tests UI."""
        # Header
        header = ttk.Frame(self.parent)
        header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(header, text="Spindle Test Procedures",
                  font=("Helvetica", 12, "bold")).pack(side=tk.LEFT)

        # Main notebook for test categories
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs for each category
        for category_name, tests in self.TEST_CATEGORIES:
            category_frame = ttk.Frame(self.notebook)
            self.notebook.add(category_frame, text=category_name)

            # Inner notebook for individual tests in this category
            inner_notebook = ttk.Notebook(category_frame)
            inner_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            for test_name, test_class, test_key in tests:
                test_frame = ttk.Frame(inner_notebook)
                inner_notebook.add(test_frame, text=test_name)
                self._setup_test_tab(test_frame, test_class, test_key)

        # Progress and results area (shared)
        bottom_frame = ttk.Frame(self.parent)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Progress indicator
        progress_frame = ttk.Frame(bottom_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Ready",
                                        font=("Arial", 9))
        self.progress_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate',
                                            length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

        # Results area
        results_frame = ttk.LabelFrame(bottom_frame, text="Test Results", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Button row
        btn_frame = ttk.Frame(results_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Clear Results",
                   command=self.clear_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Abort Test",
                   command=self.abort_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Copy",
                   command=self.copy_results).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Export...",
                   command=self.export_results_dialog).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Save Session",
                   command=self.save_session).pack(side=tk.RIGHT, padx=2)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=10,
                                                       font=("Courier", 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Mock controls (if mock mode)
        if self.hal.is_mock:
            self._setup_mock_controls(bottom_frame)

    def _setup_test_tab(self, parent: ttk.Frame, test_class, test_key: str):
        """Setup a single test tab with description and controls."""
        desc = test_class.get_description()

        # Create scrollable frame
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Title and reference
        title_frame = ttk.Frame(scrollable)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(title_frame, text=desc.name,
                  font=("Helvetica", 14, "bold")).pack(anchor="w")
        if desc.guide_ref:
            ttk.Label(title_frame, text=f"Reference: {desc.guide_ref}",
                      foreground="blue").pack(anchor="w")

        # Purpose section
        self._add_section(scrollable, "Purpose", desc.purpose)

        # Prerequisites
        if desc.prerequisites:
            self._add_list_section(scrollable, "Prerequisites", desc.prerequisites)

        # Safety notes (highlighted)
        if desc.safety_notes:
            safety_frame = ttk.LabelFrame(scrollable, text="Safety Notes", padding="10")
            safety_frame.pack(fill=tk.X, padx=10, pady=5)

            for note in desc.safety_notes:
                lbl = ttk.Label(safety_frame, text=f"  {note}",
                                foreground="red", wraplength=500)
                lbl.pack(anchor="w")

        # Procedure
        if desc.procedure:
            self._add_list_section(scrollable, "Procedure", desc.procedure)

        # Expected results
        if desc.expected_results:
            self._add_list_section(scrollable, "Expected Results", desc.expected_results)

        # Test-specific controls
        controls_frame = ttk.LabelFrame(scrollable, text="Test Controls", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Add test-specific inputs
        if test_key == "step":
            self._add_step_controls(controls_frame, test_key)
        elif test_key == "steadystate":
            self._add_steadystate_controls(controls_frame, test_key)
        else:
            # Just a run button
            ttk.Button(controls_frame, text=f"Run {desc.name}",
                       command=lambda k=test_key: self._run_test(k)).pack(pady=5)

        # Troubleshooting (collapsed by default concept, shown expanded here)
        if desc.troubleshooting:
            self._add_list_section(scrollable, "Troubleshooting", desc.troubleshooting)

    def _add_section(self, parent, title: str, content: str):
        """Add a text section."""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Clean up content
        lines = content.strip().split('\n')
        clean_lines = [line.strip() for line in lines if line.strip()]
        text = '\n'.join(clean_lines)

        lbl = ttk.Label(frame, text=text, wraplength=500, justify=tk.LEFT)
        lbl.pack(anchor="w")

    def _add_list_section(self, parent, title: str, items: list):
        """Add a bulleted list section."""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.pack(fill=tk.X, padx=10, pady=5)

        for item in items:
            # Handle indented items
            if item.startswith("  "):
                prefix = "    "
            else:
                prefix = ""

            lbl = ttk.Label(frame, text=f"{prefix}{item}",
                            wraplength=500, justify=tk.LEFT)
            lbl.pack(anchor="w")

    def _add_step_controls(self, parent, test_key: str):
        """Add step test specific controls."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=5)

        ttk.Label(row, text="From RPM:").pack(side=tk.LEFT, padx=5)
        self.step_from = ttk.Entry(row, width=8)
        self.step_from.insert(0, "500")
        self.step_from.pack(side=tk.LEFT)

        ttk.Label(row, text="To RPM:").pack(side=tk.LEFT, padx=5)
        self.step_to = ttk.Entry(row, width=8)
        self.step_to.insert(0, "1200")
        self.step_to.pack(side=tk.LEFT)

        ttk.Button(row, text="Run Step Test",
                   command=lambda: self._run_test(test_key)).pack(side=tk.LEFT, padx=20)

    def _add_steadystate_controls(self, parent, test_key: str):
        """Add steady-state test specific controls."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=5)

        ttk.Label(row, text="Duration (sec):").pack(side=tk.LEFT, padx=5)
        self.ss_duration = ttk.Entry(row, width=8)
        self.ss_duration.insert(0, "30")
        self.ss_duration.pack(side=tk.LEFT)

        ttk.Label(row, text="(10-300 seconds)").pack(side=tk.LEFT, padx=5)

        ttk.Button(row, text="Run Steady-State Test",
                   command=lambda: self._run_test(test_key)).pack(side=tk.LEFT, padx=20)

    def _setup_mock_controls(self, parent):
        """Setup mock fault simulation controls."""
        mock_frame = ttk.LabelFrame(parent, text="Mock Simulation Controls", padding="5")
        mock_frame.pack(fill=tk.X, pady=5)

        # Load simulation slider
        load_frame = ttk.Frame(mock_frame)
        load_frame.pack(fill=tk.X, pady=3)

        ttk.Label(load_frame, text="Simulated Load:").pack(side=tk.LEFT)
        self.load_slider = ttk.Scale(load_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self._update_mock_load)
        self.load_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.load_label = ttk.Label(load_frame, text="0%", width=5)
        self.load_label.pack(side=tk.LEFT)

        # Revs display
        revs_frame = ttk.Frame(mock_frame)
        revs_frame.pack(fill=tk.X, pady=3)
        ttk.Label(revs_frame, text="Revolutions:").pack(side=tk.LEFT)
        self.lbl_revs = ttk.Label(revs_frame, text="0.000",
                                   font=("Courier", 11, "bold"))
        self.lbl_revs.pack(side=tk.LEFT, padx=10)
        ttk.Button(revs_frame, text="Reset Revs",
                   command=self._reset_revs).pack(side=tk.LEFT)

        ttk.Separator(mock_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Fault toggle buttons
        ttk.Label(mock_frame, text="Toggle faults to test failure detection:").pack(anchor="w")

        btns = ttk.Frame(mock_frame)
        btns.pack(fill=tk.X, pady=5)

        faults = [
            ("encoder", "Encoder Fault"),
            ("polarity", "Polarity Reversed"),
            ("dpll", "DPLL Disabled"),
            ("vfd", "VFD Fault"),
            ("estop", "E-Stop"),
        ]

        for fault_key, fault_name in faults:
            btn = ttk.Button(btns, text=f"{fault_name}: OFF",
                             command=lambda k=fault_key: self._toggle_fault(k))
            btn.pack(side=tk.LEFT, padx=3)
            self.mock_buttons[fault_key] = btn

    def _create_test_instances(self):
        """Create instances of all test classes."""
        for category_name, tests in self.TEST_CATEGORIES:
            for test_name, test_class, test_key in tests:
                self.tests[test_key] = test_class(
                    self.hal,
                    self.logger,
                    log_callback=self.log_result,
                    progress_callback=self.update_progress
                )

        # Configure full suite with test instances
        if "full_suite" in self.tests:
            self.tests["full_suite"].set_test_instances({
                "signal_chain": self.tests.get("signal_chain"),
                "open_loop": self.tests.get("open_loop"),
                "forward": self.tests.get("forward"),
                "step": self.tests.get("step"),
            })

    def _run_test(self, test_key: str):
        """Run a specific test."""
        test = self.tests.get(test_key)
        if not test:
            self.log_result(f"Test not found: {test_key}")
            return

        # Handle test-specific parameters
        if test_key == "step":
            try:
                step_from = int(self.step_from.get())
                step_to = int(self.step_to.get())
                test.set_step_values(step_from, step_to)
            except ValueError:
                messagebox.showerror("Error", "Invalid step values")
                return

        elif test_key == "steadystate":
            try:
                duration = int(self.ss_duration.get())
                test.set_duration(duration)
            except ValueError:
                duration = 30
                test.set_duration(duration)

        test.run()

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def log_result(self, text: str):
        """Log text to results area."""
        def _update():
            if self.results_text:
                self.results_text.insert(tk.END, text + "\n")
                self.results_text.see(tk.END)
            if self.log_callback:
                self.log_callback(text)

        # Ensure UI updates happen on the main thread
        self.parent.after(0, _update)

    def clear_results(self):
        """Clear the results text area."""
        if self.results_text:
            self.results_text.delete(1.0, tk.END)

    def copy_results(self):
        """Copy results to clipboard."""
        if self.results_text:
            text = self.results_text.get(1.0, tk.END)
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)

    def update_progress(self, percent: float, message: str = ""):
        """Update progress bar and label."""
        if self.progress_bar:
            self.progress_bar['value'] = min(100, max(0, percent))
        if self.progress_label and message:
            self.progress_label.config(text=message)

    def reset_progress(self):
        """Reset progress indicator."""
        if self.progress_bar:
            self.progress_bar['value'] = 0
        if self.progress_label:
            self.progress_label.config(text="Ready")

    def abort_test(self):
        """Signal all tests to abort."""
        for test in self.tests.values():
            if test.test_running:
                test.abort()
                break

    def update_revs(self, revs: float):
        """Update revolutions display."""
        if self.lbl_revs:
            self.lbl_revs.config(text=f"{revs:.3f}")

    def _update_mock_load(self, value):
        """Update mock load percentage."""
        load = float(value)
        self.load_label.config(text=f"{load:.0f}%")
        if hasattr(self.hal, 'set_mock_load'):
            self.hal.set_mock_load(load / 100.0)
        elif hasattr(self.hal, '_mock_state'):
            self.hal._mock_state.load_factor = load / 100.0

    def _reset_revs(self):
        """Reset revolutions counter."""
        if hasattr(self.hal, '_mock_state'):
            self.hal._mock_state.revolutions = 0.0
        self.log_result("Revolutions counter reset.")

    def _toggle_fault(self, fault_key: str):
        """Toggle a mock fault."""
        if not self.hal.is_mock:
            return

        state_map = {
            'encoder': 'encoder_fault',
            'polarity': 'polarity_reversed',
            'dpll': 'dpll_disabled',
            'vfd': 'vfd_fault',
            'estop': 'estop_triggered',
        }

        attr = state_map.get(fault_key)
        if attr and hasattr(self.hal, '_mock_state'):
            current = getattr(self.hal._mock_state, attr, False)
            self.hal.set_mock_fault(fault_key, not current)
            new_state = "ON" if not current else "OFF"

            btn = self.mock_buttons.get(fault_key)
            if btn:
                name = fault_key.replace('_', ' ').title()
                btn.config(text=f"{name}: {new_state}")

            self.log_result(f"[MOCK] {fault_key}: {new_state}")

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_results_dialog(self):
        """Export test results with format selection."""
        if not self.results_text:
            messagebox.showinfo("No Results", "No test results to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile=f"spindle_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not filepath:
            return

        try:
            ext = filepath.lower().split('.')[-1]
            log_text = self.results_text.get(1.0, tk.END)

            if ext == 'json':
                data = {
                    'export_time': datetime.now().isoformat(),
                    'test_log': log_text.strip().split('\n'),
                    'parameters': self._get_current_params()
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

            elif ext == 'csv':
                lines = log_text.strip().split('\n')
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Entry'])
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    for line in lines:
                        if line.strip():
                            writer.writerow([timestamp, line])
            else:
                with open(filepath, 'w') as f:
                    f.write(f"Spindle Tuner Test Log\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(log_text)

            messagebox.showinfo("Export Complete", f"Results exported to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export results:\n{e}")

    def save_session(self):
        """Save complete test session with parameters and results."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Session files", "*.json"), ("All files", "*.*")],
            initialfile=f"spindle_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if not filepath:
            return

        try:
            session_data = {
                'session_time': datetime.now().isoformat(),
                'test_log': self.results_text.get(1.0, tk.END).strip().split('\n') if self.results_text else [],
                'current_parameters': self._get_current_params(),
                'baseline_parameters': dict(BASELINE_PARAMS),
                'hardware_specs': {
                    'motor': dict(MOTOR_SPECS),
                    'vfd': dict(VFD_SPECS),
                    'encoder': dict(ENCODER_SPECS)
                }
            }

            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)

            messagebox.showinfo("Session Saved", f"Test session saved to:\n{filepath}")
            self.log_result(f"\n[Session saved to {filepath}]")

        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save session:\n{e}")

    def _get_current_params(self) -> dict:
        """Get current PID parameters."""
        params = {}
        for param in ['P', 'I', 'FF0', 'FF1', 'Deadband', 'MaxErrorI', 'RateLimit']:
            try:
                params[param] = self.hal.get_param(param)
            except:
                params[param] = None
        return params

    # =========================================================================
    # PUBLIC METHODS FOR COMPATIBILITY
    # =========================================================================

    def run_step_test(self):
        """Run step test (for keyboard shortcut compatibility)."""
        self._run_test("step")

    def run_full_suite(self):
        """Run full suite (for keyboard shortcut compatibility)."""
        self._run_test("full_suite")
