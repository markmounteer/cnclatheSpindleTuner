#!/usr/bin/env python3
"""
Spindle Tuner - Tests & Checklists Feature

Provides automated test procedures mapped to SPINDLE_PID_TUNING_GUIDE_v5.3:

§5 Pre-Flight Verification:
  - 5.1 Signal Chain Check
  - 5.2 Encoder Direction Test (in Encoder Verification)
  - 5.4 DPLL Verification (in Pre-Flight)

§6 Initial Startup Procedures:
  - 6.1 Open-Loop Baseline Test
  - 6.2 Forward PID Test
  - 6.3 Reverse PID Test
  - 6.4 Rate Limit Verification
  - 6.5 Load Test (in Interactive Load Test)

§7 Baseline Performance Testing:
  - 7.1 Step Response (Test A)
  - 7.2 Load Recovery (Test B)
  - 7.3 Steady-State Accuracy (Test C)
  - 7.4 Performance Targets (assessment in all tests)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import json
import csv
from datetime import datetime
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass

from config import (
    MONITOR_PINS, BASELINE_PARAMS,
    HARDWARE_CHECKLIST, COMMISSIONING_CHECKLIST,
    MOTOR_SPECS, VFD_SPECS, ENCODER_SPECS
)


# =============================================================================
# PERFORMANCE TARGETS (Guide §7.4)
# =============================================================================

@dataclass
class PerformanceTargets:
    """Performance targets from Guide §7.4."""
    # Settling time targets
    settling_excellent: float = 2.0  # seconds
    settling_good: float = 3.0
    
    # Overshoot targets
    overshoot_excellent: float = 5.0  # percent
    overshoot_good: float = 10.0
    
    # Steady-state error targets
    ss_error_excellent: float = 8.0  # RPM
    ss_error_good: float = 15.0
    
    # Load recovery targets
    recovery_excellent: float = 2.0  # seconds
    recovery_good: float = 3.0
    
    # Noise targets
    noise_excellent: float = 10.0  # RPM peak-to-peak
    noise_good: float = 20.0


TARGETS = PerformanceTargets()


# =============================================================================
# TESTS TAB CLASS
# =============================================================================

class TestsTab:
    """
    Tests feature slice.
    
    Provides automated test procedures aligned with tuning guide sections:
    - Pre-Flight Checks (§5)
    - Initial Startup Tests (§6)
    - Performance Tests (§7)
    - Encoder Verification (§12)
    """
    
    def __init__(self, parent: ttk.Frame, hal_interface, data_logger,
                 log_callback: Optional[Callable] = None):
        self.parent = parent
        self.hal = hal_interface
        self.logger = data_logger
        self.log_callback = log_callback
        
        self.test_running = False
        self.test_abort = False
        self.results_text = None
        
        # UI elements
        self.step_from = None
        self.step_to = None
        self.ss_duration = None
        self.lbl_revs = None
        
        # Mock fault buttons (only in mock mode)
        self.btn_enc_fault = None
        self.btn_polarity = None
        self.btn_dpll = None
        self.btn_vfd_fault = None
        self.btn_estop = None
        self.load_slider = None
        self.load_label = None
        
        # Progress tracking
        self.progress_bar = None
        self.progress_label = None
        
        self._setup_ui()
    
    # =========================================================================
    # UI SETUP
    # =========================================================================
    
    def _setup_ui(self):
        """Build tests tab UI."""
        ttk.Label(self.parent, text="Automated Test Procedures",
                 font=("Helvetica", 12, "bold")).pack(pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.parent)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>",
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Four-column layout
        columns = ttk.Frame(scrollable)
        columns.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self._setup_preflight_tests(columns)
        self._setup_startup_tests(columns)
        self._setup_performance_tests(columns)
        self._setup_advanced_tests(columns)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mock fault controls (if mock mode)
        if self.hal.is_mock:
            self._setup_mock_controls()
        
        # Progress indicator
        progress_frame = ttk.Frame(self.parent)
        progress_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready", 
                                        font=("Arial", 9))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', 
                                            length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        
        # Results area with abort button
        results_frame = ttk.LabelFrame(self.parent, text="Test Results", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(results_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Clear Results",
                  command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Abort Test",
                  command=self.abort_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save Session",
                  command=self.save_session).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Export...",
                  command=self.export_results_dialog).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Copy",
                  command=self.copy_results).pack(side=tk.RIGHT, padx=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=12,
                                                       font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _setup_preflight_tests(self, parent: ttk.Frame):
        """Setup pre-flight verification tests (Guide §5)."""
        col = ttk.LabelFrame(parent, text="1. Pre-Flight (§5)", padding="5")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Signal chain check
        ttk.Label(col, text="Signal Chain (§5.1)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="Verifies HAL connections",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="Signal Chain Check",
                  command=self.run_signal_chain_check).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Pre-flight check
        ttk.Label(col, text="Full Pre-Flight (§5, §14.3)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="Run before tuning session",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="✓ Pre-Flight Check",
                  command=self.run_preflight_check).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Encoder verification
        ttk.Label(col, text="Encoder (§5.2, §12.2)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="Direction + DPLL test",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="Encoder Verification",
                  command=self.run_encoder_verification).pack(fill=tk.X, pady=3)
    
    def _setup_startup_tests(self, parent: ttk.Frame):
        """Setup initial startup tests (Guide §6)."""
        col = ttk.LabelFrame(parent, text="2. Startup (§6)", padding="5")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Open loop baseline
        ttk.Label(col, text="Open Loop (§6.1)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="FF0 only, measures slip",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="Open Loop Check",
                  command=self.run_open_loop).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Forward/Reverse PID
        ttk.Label(col, text="Direction Tests (§6.2-6.3)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Button(col, text="Forward PID Test (M3)",
                  command=self.run_forward_test).pack(fill=tk.X, pady=3)
        ttk.Button(col, text="⚠️ Reverse PID Test (M4)",
                  command=self.run_reverse_test).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Rate limit
        ttk.Label(col, text="Rate Limit (§6.4)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="Verifies limit2 ramp rate",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="Rate Limit Test",
                  command=self.run_rate_limit_test).pack(fill=tk.X, pady=3)
    
    def _setup_performance_tests(self, parent: ttk.Frame):
        """Setup baseline performance tests (Guide §7)."""
        col = ttk.LabelFrame(parent, text="3. Performance (§7)", padding="5")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Step response
        ttk.Label(col, text="Step Response (§7.1)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        
        step_frame = ttk.Frame(col)
        step_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step_frame, text="From:").pack(side=tk.LEFT)
        self.step_from = ttk.Entry(step_frame, width=6)
        self.step_from.insert(0, "500")
        self.step_from.pack(side=tk.LEFT, padx=2)
        ttk.Label(step_frame, text="To:").pack(side=tk.LEFT)
        self.step_to = ttk.Entry(step_frame, width=6)
        self.step_to.insert(0, "1200")
        self.step_to.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(col, text="Run Step Test (F5)",
                  command=self.run_step_test).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Load recovery
        ttk.Label(col, text="Load Recovery (§7.2)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(col, text="Apply friction when prompted",
                 foreground="blue", font=("Arial", 8)).pack(anchor="w")
        ttk.Button(col, text="Interactive Load Test",
                  command=self.run_load_test).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Steady-state
        ttk.Label(col, text="Steady-State (§7.3)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        
        ss_frame = ttk.Frame(col)
        ss_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ss_frame, text="Duration:").pack(side=tk.LEFT)
        self.ss_duration = ttk.Entry(ss_frame, width=5)
        self.ss_duration.insert(0, "30")
        self.ss_duration.pack(side=tk.LEFT, padx=2)
        ttk.Label(ss_frame, text="sec").pack(side=tk.LEFT)
        
        ttk.Button(col, text="Steady-State Monitor",
                  command=self.run_steadystate_test).pack(fill=tk.X, pady=3)
    
    def _setup_advanced_tests(self, parent: ttk.Frame):
        """Setup advanced and additional tests."""
        col = ttk.LabelFrame(parent, text="4. Advanced", padding="5")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Additional response tests
        ttk.Label(col, text="Response Tests",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Button(col, text="Decel Test (1200→0)",
                  command=self.run_decel_test).pack(fill=tk.X, pady=3)
        ttk.Button(col, text="Full Ramp (0→1800→0)",
                  command=self.run_ramp_test).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Threading check
        ttk.Label(col, text="Threading (§10.2)",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        
        revs_frame = ttk.Frame(col)
        revs_frame.pack(fill=tk.X, pady=3)
        ttk.Label(revs_frame, text="Revs:").pack(side=tk.LEFT)
        self.lbl_revs = ttk.Label(revs_frame, text="0.000",
                                   font=("Courier", 12, "bold"))
        self.lbl_revs.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(col, text="Reset Revs Counter",
                  command=self.reset_revs_counter).pack(fill=tk.X, pady=3)
        
        ttk.Separator(col, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Quick test suite
        ttk.Label(col, text="Full Test Suite",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Button(col, text="▶ Run All Tests",
                  command=self.run_full_suite).pack(fill=tk.X, pady=3)
    
    def _setup_mock_controls(self):
        """Setup mock fault simulation controls."""
        mock_frame = ttk.LabelFrame(self.parent, text="Mock Simulation Controls", padding="5")
        mock_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Load simulation slider
        load_frame = ttk.Frame(mock_frame)
        load_frame.pack(fill=tk.X, pady=3)
        
        ttk.Label(load_frame, text="Simulated Load:",
                 font=("Arial", 9)).pack(side=tk.LEFT)
        self.load_slider = ttk.Scale(load_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self._update_mock_load)
        self.load_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.load_label = ttk.Label(load_frame, text="0%", width=5)
        self.load_label.pack(side=tk.LEFT)
        
        ttk.Separator(mock_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Label(mock_frame, text="Toggle faults to test failure detection:",
                 font=("Arial", 9)).pack(anchor="w")
        
        btns = ttk.Frame(mock_frame)
        btns.pack(fill=tk.X, pady=5)
        
        self.btn_enc_fault = ttk.Button(btns, text="Encoder Fault: OFF",
                                        command=self.toggle_encoder_fault)
        self.btn_enc_fault.pack(side=tk.LEFT, padx=3)
        
        self.btn_polarity = ttk.Button(btns, text="Polarity Reversed: OFF",
                                       command=self.toggle_polarity_fault)
        self.btn_polarity.pack(side=tk.LEFT, padx=3)
        
        self.btn_dpll = ttk.Button(btns, text="DPLL Disabled: OFF",
                                   command=self.toggle_dpll_fault)
        self.btn_dpll.pack(side=tk.LEFT, padx=3)
        
        self.btn_vfd_fault = ttk.Button(btns, text="VFD Fault: OFF",
                                        command=self.toggle_vfd_fault)
        self.btn_vfd_fault.pack(side=tk.LEFT, padx=3)
        
        self.btn_estop = ttk.Button(btns, text="E-Stop: OFF",
                                    command=self.toggle_estop)
        self.btn_estop.pack(side=tk.LEFT, padx=3)
        
        ttk.Separator(mock_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Safe mock-only watchdog test
        ttk.Label(mock_frame, text="Safe Watchdog Test (mock only):",
                 font=("Arial", 9)).pack(anchor="w")
        ttk.Button(mock_frame, text="🔒 Simulate Encoder Watchdog Trip (§6.6)",
                  command=self.run_mock_watchdog_test).pack(fill=tk.X, pady=3)
    
    def _update_mock_load(self, value):
        """Update mock load percentage."""
        load = float(value)
        self.load_label.config(text=f"{load:.0f}%")
        # Update mock state if method exists
        if hasattr(self.hal, 'set_mock_load'):
            self.hal.set_mock_load(load / 100.0)
        elif hasattr(self.hal, '_mock_state'):
            self.hal._mock_state.load_factor = load / 100.0
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def log_result(self, text: str):
        """Log text to results area."""
        if self.results_text:
            self.results_text.insert(tk.END, text + "\n")
            self.results_text.see(tk.END)
        if self.log_callback:
            self.log_callback(text)
    
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
    
    def export_results(self):
        """Export test results to a text file."""
        if not self.results_text:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"spindle_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(f"Spindle Tuner Test Log\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(self.results_text.get(1.0, tk.END))
                messagebox.showinfo("Export Complete", f"Log exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export log:\n{e}")
    
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
                # Export as structured JSON
                data = {
                    'export_time': datetime.now().isoformat(),
                    'test_log': log_text.strip().split('\n'),
                    'parameters': self._get_current_params()
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            elif ext == 'csv':
                # Export as CSV (parse log for structured data)
                lines = log_text.strip().split('\n')
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Entry'])
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    for line in lines:
                        if line.strip():
                            writer.writerow([timestamp, line])
            else:
                # Default text export
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
        """Signal test to abort."""
        if self.test_running:
            self.test_abort = True
            self.log_result("\n⏹ ABORT REQUESTED - stopping spindle...")
            self.hal.send_mdi("M5")
    
    def update_revs(self, revs: float):
        """Update revolutions display."""
        if self.lbl_revs:
            self.lbl_revs.config(text=f"{revs:.3f}")
    
    def _sample_signal(self, pin_name: str, duration: float, 
                       interval: float = 0.1) -> Tuple[List[float], List[float]]:
        """Sample a HAL pin for a given duration."""
        samples = []
        times = []
        start = time.time()
        
        while time.time() - start < duration:
            if self.test_abort:
                break
            val = self.hal.get_pin_value(pin_name)
            samples.append(val)
            times.append(time.time() - start)
            time.sleep(interval)
        
        return times, samples
    
    def _assess_settling(self, settling_time: float) -> str:
        """Assess settling time per Guide §7.4."""
        if settling_time <= TARGETS.settling_excellent:
            return f"EXCELLENT (≤{TARGETS.settling_excellent}s)"
        elif settling_time <= TARGETS.settling_good:
            return f"GOOD (≤{TARGETS.settling_good}s)"
        else:
            return f"SLOW (>{TARGETS.settling_good}s)"
    
    def _assess_overshoot(self, overshoot_pct: float) -> str:
        """Assess overshoot per Guide §7.4."""
        if overshoot_pct <= TARGETS.overshoot_excellent:
            return f"EXCELLENT (≤{TARGETS.overshoot_excellent}%)"
        elif overshoot_pct <= TARGETS.overshoot_good:
            return f"GOOD (≤{TARGETS.overshoot_good}%)"
        else:
            return f"HIGH (>{TARGETS.overshoot_good}%)"
    
    def _assess_ss_error(self, error_rpm: float) -> str:
        """Assess steady-state error per Guide §7.4."""
        abs_error = abs(error_rpm)
        if abs_error <= TARGETS.ss_error_excellent:
            return f"EXCELLENT (≤{TARGETS.ss_error_excellent} RPM)"
        elif abs_error <= TARGETS.ss_error_good:
            return f"GOOD (≤{TARGETS.ss_error_good} RPM)"
        else:
            return f"HIGH (>{TARGETS.ss_error_good} RPM)"
    
    def _assess_recovery(self, recovery_time: float) -> str:
        """Assess load recovery time per Guide §7.4."""
        if recovery_time <= TARGETS.recovery_excellent:
            return f"EXCELLENT (≤{TARGETS.recovery_excellent}s)"
        elif recovery_time <= TARGETS.recovery_good:
            return f"GOOD (≤{TARGETS.recovery_good}s)"
        else:
            return f"SLOW (>{TARGETS.recovery_good}s)"
    
    def _start_test(self, name: str) -> bool:
        """Start a test if none running."""
        if self.test_running:
            messagebox.showinfo("Info", "A test is already running.")
            return False
        self.test_running = True
        self.test_abort = False
        return True
    
    def _end_test(self):
        """Mark test as complete."""
        self.test_running = False
        self.test_abort = False
    
    # =========================================================================
    # PRE-FLIGHT TESTS (Guide §5)
    # =========================================================================
    
    def run_signal_chain_check(self):
        """Run signal chain validation (Guide §5.1)."""
        if not self._start_test("Signal Chain"):
            return
        threading.Thread(target=self._signal_chain_sequence, daemon=True).start()
    
    def _signal_chain_sequence(self):
        """Execute signal chain check."""
        self.log_result(f"\n{'='*50}")
        self.log_result("SIGNAL CHAIN CHECK (Guide §5.1)")
        self.log_result("="*50)
        
        pass_count = 0
        fail_count = 0
        
        checks = [
            (MONITOR_PINS.get('cmd_raw', 'spindle-vel-cmd-rpm-raw'), 
             "Command signal", lambda v: True),
            (MONITOR_PINS.get('cmd_limited', 'spindle-vel-cmd-rpm-limited'),
             "Rate-limited command", lambda v: True),
            (MONITOR_PINS.get('feedback', 'spindle-vel-fb-rpm'),
             "Velocity feedback", lambda v: True),
            (MONITOR_PINS.get('feedback_abs', 'spindle-vel-fb-rpm-abs'),
             "ABS feedback", lambda v: True),
            (MONITOR_PINS.get('error', 'pid.s.error'),
             "PID error signal", lambda v: True),
            (MONITOR_PINS.get('errorI', 'pid.s.errorI'),
             "PID integrator", lambda v: True),
            (MONITOR_PINS.get('output', 'pid.s.output'),
             "PID output", lambda v: True),
            (MONITOR_PINS.get('at_speed', 'spindle-is-at-speed'),
             "At-speed indicator", lambda v: v in [0.0, 1.0]),
        ]
        
        self.log_result("\nVerifying HAL signal chain:")
        
        for pin_name, desc, validator in checks:
            try:
                value = self.hal.get_pin_value(pin_name)
                if validator(value):
                    self.log_result(f"  ✓ {desc}: {value:.2f}")
                    pass_count += 1
                else:
                    self.log_result(f"  ⚠ {desc}: {value:.2f} (unexpected)")
                    fail_count += 1
            except Exception as e:
                self.log_result(f"  ✗ {desc}: ERROR - {e}")
                fail_count += 1
        
        self.log_result("\nVerifying PID parameters loaded:")
        for param in ['P', 'I', 'FF0', 'FF1']:
            value = self.hal.get_param(param)
            expected = BASELINE_PARAMS.get(param, 0)
            if value > 0 or param in ['P']:
                self.log_result(f"  ✓ {param}: {value:.3f}")
                pass_count += 1
            else:
                self.log_result(f"  ⚠ {param}: {value:.3f} (expected ~{expected})")
                fail_count += 1
        
        self.log_result(f"\n{'='*50}")
        total = pass_count + fail_count
        if fail_count == 0:
            self.log_result(f"SIGNAL CHAIN: ✓ ALL {pass_count} CHECKS PASSED")
        else:
            self.log_result(f"SIGNAL CHAIN: ⚠ {fail_count}/{total} ISSUES FOUND")
        self.log_result("="*50)
        
        self._end_test()
    
    def run_preflight_check(self):
        """Run pre-flight verification (Guide §5, §14.3)."""
        if not self._start_test("Pre-Flight"):
            return
        threading.Thread(target=self._preflight_sequence, daemon=True).start()
    
    def _preflight_sequence(self):
        """Execute pre-flight checks."""
        self.log_result(f"\n{'='*50}")
        self.log_result("PRE-FLIGHT CHECK (Guide §5, §14.3)")
        self.log_result("="*50)
        
        all_ok = True
        
        # 1. Check PID parameters vs baseline
        self.log_result("\n1. PID Parameters vs Baseline:")
        for param in ['P', 'I', 'FF0', 'FF1', 'Deadband', 'MaxErrorI', 'RateLimit']:
            current = self.hal.get_param(param)
            expected = BASELINE_PARAMS.get(param, 0)
            diff_pct = abs(current - expected) / max(expected, 0.001) * 100
            
            if diff_pct < 25:
                status = "✓ OK"
            elif diff_pct < 50:
                status = "⚠ DIFFERS"
                all_ok = False
            else:
                status = "✗ FAR OFF"
                all_ok = False
            
            self.log_result(f"   {param}: {current:.3f} (baseline {expected}) - {status}")
        
        # 2. DPLL verification (Guide §5.4)
        self.log_result("\n2. DPLL Configuration (§5.4):")
        dpll_timer = self.hal.get_pin_value('hm2_7i76e.0.dpll.01.timer-us')
        if abs(dpll_timer - (-100)) < 20 or abs(dpll_timer - 100) < 20:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}µs - ✓ OK")
        elif dpll_timer == 0:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}µs - ⚠ MAY BE DISABLED")
            all_ok = False
        else:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}µs - ✓ Non-zero")
        
        # 3. Safety signals
        self.log_result("\n3. Safety Signals:")
        ext_ok = self.hal.get_pin_value(MONITOR_PINS.get('external_ok', 'external-ok'))
        
        if ext_ok > 0.5:
            self.log_result(f"   external-ok: {ext_ok:.0f} - ✓ OK")
        else:
            self.log_result(f"   external-ok: {ext_ok:.0f} - ✗ NOT OK")
            all_ok = False
        
        # 4. Brief spin test
        self.log_result("\n4. Brief Spin Test:")
        self.log_result("   Starting M3 S200...")
        self.hal.send_mdi("M3 S200")
        time.sleep(3.0)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self.log_result("   ABORTED")
            self._end_test()
            return
        
        fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        fb_abs = self.hal.get_pin_value(MONITOR_PINS['feedback_abs'])
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])
        
        self.hal.send_mdi("M5")
        
        if fb > 100:
            self.log_result(f"   Feedback: {fb:.0f} RPM - ✓ OK")
        else:
            self.log_result(f"   Feedback: {fb:.0f} RPM - ✗ LOW/WRONG")
            all_ok = False
        
        if fb_abs > 100:
            self.log_result(f"   ABS feedback: {fb_abs:.0f} RPM - ✓ OK")
        else:
            self.log_result(f"   ABS feedback: {fb_abs:.0f} RPM - ✗ CHECK")
            all_ok = False
        
        if at_speed > 0.5:
            self.log_result(f"   At-speed: YES - ✓ OK")
        else:
            self.log_result(f"   At-speed: NO - ⚠ Did not reach speed")
        
        self.log_result(f"\n{'='*50}")
        if all_ok:
            self.log_result("PRE-FLIGHT: ✓ ALL CHECKS PASSED")
            self.log_result("Ready for tuning session.")
        else:
            self.log_result("PRE-FLIGHT: ⚠ ISSUES FOUND")
            self.log_result("Review warnings before proceeding.")
        self.log_result("="*50)
        
        self._end_test()
    
    def run_encoder_verification(self):
        """Run encoder verification test (Guide §5.2, §12.2)."""
        if not self._start_test("Encoder Verification"):
            return
        threading.Thread(target=self._encoder_sequence, daemon=True).start()
    
    def _encoder_sequence(self):
        """Execute encoder verification."""
        self.log_result(f"\n{'='*50}")
        self.log_result("ENCODER VERIFICATION (Guide §5.2, §12.2)")
        self.log_result("="*50)
        
        speeds = [
            (100, "Low speed - DPLL sensitive"),
            (500, "Mid speed"),
            (1500, "High speed")
        ]
        results = []
        
        for target, desc in speeds:
            if self.test_abort:
                break
                
            self.log_result(f"\nTesting {target} RPM ({desc})...")
            self.hal.send_mdi(f"M3 S{target}")
            time.sleep(3.5)
            
            _, samples = self._sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
            
            if not samples:
                self.log_result(f"   ✗ No samples collected")
                continue
            
            avg = sum(samples) / len(samples)
            noise = max(samples) - min(samples)
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0
            
            results.append({
                'target': target, 
                'avg': avg, 
                'noise': noise, 
                'error_pct': error_pct
            })
            
            if avg < 0:
                self.log_result(f"   ✗ NEGATIVE feedback: {avg:.1f} RPM")
                self.log_result(f"     → Encoder polarity REVERSED")
            else:
                self.log_result(f"   Actual: {avg:.1f} RPM (error: {error_pct:.1f}%)")
                self.log_result(f"   Noise: ±{noise/2:.1f} RPM (peak-to-peak: {noise:.1f})")
        
        self.hal.send_mdi("M5")
        
        if not results:
            self.log_result("\n✗ No valid results collected")
            self._end_test()
            return
        
        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")
        
        low_result = results[0] if results else None
        if low_result:
            if low_result['noise'] > TARGETS.noise_good:
                self.log_result(f"  ⚠ HIGH LOW-SPEED NOISE ({low_result['noise']:.0f} RPM)")
                self.log_result("    → Check DPLL configuration (Guide §5.4)")
            elif low_result['noise'] > TARGETS.noise_excellent:
                self.log_result(f"  ⚠ Moderate low-speed noise ({low_result['noise']:.0f} RPM)")
            else:
                self.log_result(f"  ✓ Low-speed noise OK ({low_result['noise']:.0f} RPM)")
        
        for r in results:
            if r['avg'] < 0:
                self.log_result(f"  ✗ NEGATIVE FEEDBACK at {r['target']} RPM")
                self.log_result("    → Encoder polarity REVERSED")
                self.log_result("    → Fix: Negate ENCODER_SCALE or swap A/B wires")
                break
        else:
            self.log_result("  ✓ Encoder polarity CORRECT (positive in M3)")
        
        high_error = max(r['error_pct'] for r in results)
        if high_error > 10:
            self.log_result(f"  ⚠ High speed error ({high_error:.1f}%)")
            self.log_result("    → Check ENCODER_SCALE matches actual PPR")
        elif high_error > 5:
            self.log_result(f"  ⚠ Moderate speed error ({high_error:.1f}%)")
        else:
            self.log_result(f"  ✓ Speed accuracy OK (max error {high_error:.1f}%)")
        
        self.log_result("="*50)
        self._end_test()
    
    # =========================================================================
    # STARTUP TESTS (Guide §6)
    # =========================================================================
    
    def run_open_loop(self):
        """Run open loop check (Guide §6.1)."""
        if not self._start_test("Open Loop"):
            return
        threading.Thread(target=self._open_loop_sequence, daemon=True).start()
    
    def _open_loop_sequence(self):
        """Execute open loop check."""
        self.log_result(f"\n{'='*50}")
        self.log_result("OPEN LOOP CHECK (Guide §6.1)")
        self.log_result("="*50)
        self.log_result("Measuring motor slip with FF0 only (no PID correction)")
        
        p_orig = self.hal.get_param('P')
        i_orig = self.hal.get_param('I')
        ff0_orig = self.hal.get_param('FF0')
        
        self.log_result("\nSetting: P=0, I=0, FF0=1.0...")
        self.hal.set_param('P', 0)
        self.hal.set_param('I', 0)
        self.hal.set_param('FF0', 1.0)
        
        self.hal.send_mdi("M3 S1000")
        self.log_result("Commanding 1000 RPM...")
        time.sleep(4)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self.hal.set_param('P', p_orig)
            self.hal.set_param('I', i_orig)
            self.hal.set_param('FF0', ff0_orig)
            self._end_test()
            return
        
        _, fb_samples = self._sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
        cmd = self.hal.get_pin_value(MONITOR_PINS['cmd_limited'])
        
        self.hal.send_mdi("M5")
        
        if fb_samples:
            fb = sum(fb_samples) / len(fb_samples)
            fb_noise = max(fb_samples) - min(fb_samples)
        else:
            fb = 0
            fb_noise = 0
        
        slip = ((cmd - fb) / cmd * 100) if cmd > 0 else 0
        expected_slip = MOTOR_SPECS['cold_slip_pct']
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Command: {cmd:.0f} RPM")
        self.log_result(f"  Feedback: {fb:.0f} RPM (noise: ±{fb_noise/2:.1f})")
        self.log_result(f"  Measured slip: {slip:.1f}%")
        self.log_result(f"  Expected cold slip: {expected_slip:.1f}%")
        
        if 1.5 <= slip <= 5.0:
            self.log_result("\n✓ PASS: Slip within normal range (1.5-5%)")
            self.log_result("  FF0=1.0 is appropriate baseline")
        elif slip < 1.5:
            self.log_result(f"\n⚠ LOW SLIP: {slip:.1f}%")
            self.log_result("  Possible causes:")
            self.log_result("  - Encoder scale too high")
            self.log_result("  - VFD output frequency offset")
        elif slip > 5.0:
            self.log_result(f"\n⚠ HIGH SLIP: {slip:.1f}%")
            self.log_result("  Possible causes:")
            self.log_result("  - Motor under load")
            self.log_result("  - Encoder scale too low")
            self.log_result("  - Motor overheating")
        
        self.hal.set_param('P', p_orig)
        self.hal.set_param('I', i_orig)
        self.hal.set_param('FF0', ff0_orig)
        self.log_result("\nParameters restored.")
        self.log_result("="*50)
        
        self._end_test()
    
    def run_forward_test(self):
        """Run forward PID test (Guide §6.2)."""
        if not self._start_test("Forward PID"):
            return
        threading.Thread(target=self._forward_sequence, daemon=True).start()
    
    def _forward_sequence(self):
        """Execute forward PID test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("FORWARD PID TEST (Guide §6.2)")
        self.log_result("="*50)
        
        self.hal.send_mdi("M3 S1000")
        self.log_result("Starting M3 S1000...")
        time.sleep(4)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        _, fb_samples = self._sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
        _, err_samples = self._sample_signal(MONITOR_PINS['error'], 1.0, 0.1)
        
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])
        errorI = self.hal.get_pin_value(MONITOR_PINS['errorI'])
        
        self.hal.send_mdi("M5")
        
        if fb_samples:
            fb_avg = sum(fb_samples) / len(fb_samples)
            fb_noise = max(fb_samples) - min(fb_samples)
        else:
            fb_avg = 0
            fb_noise = 0
        
        if err_samples:
            err_avg = sum(err_samples) / len(err_samples)
        else:
            err_avg = 0
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Feedback: {fb_avg:.1f} RPM (noise: ±{fb_noise/2:.1f})")
        self.log_result(f"  Steady-state error: {err_avg:.1f} RPM")
        self.log_result(f"  Integrator: {errorI:.1f}")
        self.log_result(f"  At-speed: {'YES' if at_speed > 0.5 else 'NO'}")
        
        all_ok = True
        
        if fb_avg > 900:
            self.log_result("\n✓ Speed reached target")
        else:
            self.log_result(f"\n✗ Speed low: {fb_avg:.0f} RPM (expected ~1000)")
            all_ok = False
        
        if at_speed > 0.5:
            self.log_result("✓ At-speed signal active")
        else:
            self.log_result("⚠ At-speed signal not active")
            all_ok = False
        
        if abs(err_avg) < 20:
            self.log_result(f"✓ Error small: {err_avg:.1f} RPM")
        else:
            self.log_result(f"⚠ Error large: {err_avg:.1f} RPM")
        
        if all_ok:
            self.log_result("\n✓ FORWARD PID: PASS")
        else:
            self.log_result("\n⚠ FORWARD PID: Issues detected")
        
        self.log_result("="*50)
        self._end_test()
    
    def run_reverse_test(self):
        """Run reverse safety test (Guide §6.3)."""
        if not self._start_test("Reverse PID"):
            return
        
        if not messagebox.askyesno("Reverse Safety Test",
                                   "This test runs spindle in REVERSE (M4).\n\n"
                                   "⚠️ Keep hand on E-stop!\n\n"
                                   "Continue?"):
            self._end_test()
            return
        
        threading.Thread(target=self._reverse_sequence, daemon=True).start()
    
    def _reverse_sequence(self):
        """Execute reverse safety test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("REVERSE PID TEST (Guide §6.3)")
        self.log_result("="*50)
        
        self.hal.send_mdi("M4 S500")
        self.log_result("Starting M4 S500 (reverse)...")
        time.sleep(3.5)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        fb_raw = self.hal.get_pin_value(MONITOR_PINS.get('feedback_raw', 'spindle-vel-fb-rpm'))
        fb_abs = self.hal.get_pin_value(MONITOR_PINS['feedback_abs'])
        pid_fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])
        
        self.hal.send_mdi("M5")
        
        self.log_result(f"\nSignal Readings:")
        self.log_result(f"  Raw feedback: {fb_raw:.1f} RPM (expect NEGATIVE)")
        self.log_result(f"  ABS feedback: {fb_abs:.1f} RPM (expect POSITIVE)")
        self.log_result(f"  PID feedback: {pid_fb:.1f} RPM (expect POSITIVE)")
        self.log_result(f"  At-speed: {'YES' if at_speed > 0.5 else 'NO'}")
        
        if fb_raw < -100 and fb_abs > 100 and pid_fb > 100:
            self.log_result(f"\n{'='*50}")
            self.log_result("✓ REVERSE TEST: PASS")
            self.log_result("  Encoder polarity: CORRECT")
            self.log_result("  ABS component: WORKING")
            self.log_result("  PID sees positive feedback for control")
        elif fb_raw > 0:
            self.log_result(f"\n{'='*50}")
            self.log_result("✗ REVERSE TEST: FAIL")
            self.log_result("  Raw feedback should be NEGATIVE in reverse")
            self.log_result("  → Encoder polarity is REVERSED")
            self.log_result("  → Fix: Negate ENCODER_SCALE or swap A/B")
        elif fb_abs < 100:
            self.log_result(f"\n{'='*50}")
            self.log_result("⚠ REVERSE TEST: ABS ISSUE")
            self.log_result("  ABS feedback should be positive magnitude")
            self.log_result("  → Check ABS component in custom.hal")
        else:
            self.log_result(f"\n{'='*50}")
            self.log_result("⚠ REVERSE TEST: Check signals")
        
        self.log_result("="*50)
        self._end_test()
    
    def run_rate_limit_test(self):
        """Run rate limit verification (Guide §6.4)."""
        if not self._start_test("Rate Limit"):
            return
        threading.Thread(target=self._rate_limit_sequence, daemon=True).start()
    
    def _rate_limit_sequence(self):
        """Execute rate limit test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("RATE LIMIT TEST (Guide §6.4)")
        self.log_result("="*50)
        self.log_result("Verifies limit2 component enforces RATE_LIMIT")
        
        self.hal.send_mdi("M5")
        time.sleep(1.0)
        
        target = 1500
        rate_limit_cfg = self.hal.get_param('RateLimit')
        
        self.log_result(f"\nConfigured RATE_LIMIT: {rate_limit_cfg:.0f} RPM/s")
        self.log_result(f"Commanding M3 S{target}...")
        
        start_time = time.time()
        times = []
        limited_vals = []
        
        self.hal.send_mdi(f"M3 S{target}")
        
        duration = 3.0
        while time.time() - start_time < duration:
            if self.test_abort:
                break
            
            t = time.time() - start_time
            limited = self.hal.get_pin_value(MONITOR_PINS['cmd_limited'])
            
            times.append(t)
            limited_vals.append(limited)
            time.sleep(0.05)
        
        self.hal.send_mdi("M5")
        
        if len(times) < 5 or self.test_abort:
            self.log_result("  Not enough samples or aborted")
            self._end_test()
            return
        
        threshold_10 = target * 0.1
        threshold_90 = target * 0.9
        t_10 = None
        t_90 = None
        
        for i, (t, v) in enumerate(zip(times, limited_vals)):
            if t_10 is None and v >= threshold_10:
                t_10 = t
            if t_90 is None and v >= threshold_90:
                t_90 = t
                break
        
        if t_10 is not None and t_90 is not None and t_90 > t_10:
            ramp_time = t_90 - t_10
            ramp_distance = threshold_90 - threshold_10
            observed_rate = ramp_distance / ramp_time
        else:
            elapsed = times[-1] - times[0]
            delta_limited = limited_vals[-1] - limited_vals[0]
            observed_rate = delta_limited / elapsed if elapsed > 0 else 0
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Limited final: {limited_vals[-1]:.0f} RPM")
        self.log_result(f"  Observed ramp rate: {observed_rate:.0f} RPM/s")
        self.log_result(f"  Configured rate: {rate_limit_cfg:.0f} RPM/s")
        
        if rate_limit_cfg > 0:
            rate_error = abs(observed_rate - rate_limit_cfg) / rate_limit_cfg
            
            if rate_error < 0.25:
                self.log_result(f"\n✓ PASS: Ramp rate within 25% of configured")
                self.log_result("  limit2 component is working correctly")
            elif rate_error < 0.50:
                self.log_result(f"\n⚠ MARGINAL: Ramp rate within 50% of configured")
                self.log_result("  Check limit2 wiring in custom.hal")
            else:
                self.log_result(f"\n✗ FAIL: Ramp rate differs significantly")
                self.log_result("  Verify limit2.0.maxv is set from RATE_LIMIT")
        else:
            self.log_result("\n⚠ Cannot evaluate - RATE_LIMIT not configured")
        
        self.log_result("="*50)
        self._end_test()
    
    # =========================================================================
    # PERFORMANCE TESTS (Guide §7)
    # =========================================================================
    
    def run_step_test(self):
        """Run step response test (Guide §7.1)."""
        if not self._start_test("Step Response"):
            return
        
        try:
            start = int(self.step_from.get())
            end = int(self.step_to.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid step values")
            self._end_test()
            return
        
        if start == end:
            messagebox.showerror("Error", "Start and end must differ")
            self._end_test()
            return
        
        threading.Thread(target=self._step_sequence, args=(start, end), daemon=True).start()
    
    def _step_sequence(self, start: int, end: int):
        """Execute step response test."""
        self.log_result(f"\n{'='*50}")
        self.log_result(f"STEP RESPONSE TEST: {start} → {end} RPM (Guide §7.1)")
        self.log_result("="*50)
        
        self.hal.send_mdi(f"M3 S{start}")
        self.log_result(f"Stabilizing at {start} RPM...")
        time.sleep(3)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        test_data = []
        
        self.log_result(f"Stepping to {end} RPM...")
        step_time = time.time()
        self.hal.send_mdi(f"M3 S{end}")
        
        while time.time() - step_time < 5.0:
            if self.test_abort:
                break
            
            t = time.time() - step_time
            values = self.hal.get_all_values()
            test_data.append({
                'time': t,
                'cmd': values.get('cmd_limited', 0),
                'feedback': values.get('feedback', 0),
                'error': values.get('error', 0),
                'errorI': values.get('errorI', 0),
            })
            time.sleep(0.1)
        
        self.hal.send_mdi("M5")
        
        if not test_data or self.test_abort:
            self.log_result("  Test aborted or no data")
            self._end_test()
            return
        
        metrics = self._calculate_step_metrics(start, end, test_data)
        
        self.log_result(f"\nRESULTS:")
        self.log_result(f"  Rise time (10-90%): {metrics['rise_time']:.2f} s")
        self.log_result(f"  Settling time (2%): {metrics['settling_time']:.2f} s")
        self.log_result(f"  Overshoot: {metrics['overshoot']:.1f}%")
        self.log_result(f"  Steady-state error: {metrics['ss_error']:.1f} RPM")
        self.log_result(f"  Max error during step: {metrics['max_error']:.1f} RPM")
        
        self.log_result(f"\nASSESSMENT (Guide §7.4):")
        self.log_result(f"  Settling: {self._assess_settling(metrics['settling_time'])}")
        self.log_result(f"  Overshoot: {self._assess_overshoot(metrics['overshoot'])}")
        self.log_result(f"  SS Error: {self._assess_ss_error(metrics['ss_error'])}")
        
        if (metrics['settling_time'] <= TARGETS.settling_excellent and 
            metrics['overshoot'] <= TARGETS.overshoot_excellent):
            self.log_result("\n✓ EXCELLENT: Fast settling, minimal overshoot")
        elif (metrics['settling_time'] <= TARGETS.settling_good and 
              metrics['overshoot'] <= TARGETS.overshoot_good):
            self.log_result("\n✓ GOOD: Acceptable performance")
        else:
            self.log_result("\n⚠ NEEDS TUNING: See troubleshooter for suggestions")
        
        self.log_result("="*50)
        self._end_test()
    
    def _calculate_step_metrics(self, start: int, end: int, 
                                data: List[Dict]) -> Dict[str, float]:
        """Calculate step response metrics."""
        step_size = abs(end - start)
        feedbacks = [d['feedback'] for d in data]
        times = [d['time'] for d in data]
        
        threshold_10 = start + 0.1 * (end - start)
        threshold_90 = start + 0.9 * (end - start)
        
        t_10 = None
        t_90 = None
        
        for t, fb in zip(times, feedbacks):
            if t_10 is None and fb >= threshold_10:
                t_10 = t
            if t_90 is None and fb >= threshold_90:
                t_90 = t
                break
        
        rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else 0
        
        tolerance = 0.02 * abs(end)
        settling_time = times[-1]
        
        for i in range(len(feedbacks) - 1, -1, -1):
            if abs(feedbacks[i] - end) > tolerance:
                if i + 1 < len(times):
                    settling_time = times[i + 1]
                break
        else:
            settling_time = times[0] if times else 0
        
        if end > start:
            max_fb = max(feedbacks)
            overshoot = max(0, (max_fb - end) / step_size * 100)
        else:
            min_fb = min(feedbacks)
            overshoot = max(0, (end - min_fb) / step_size * 100)
        
        last_second = [d for d in data if d['time'] > times[-1] - 1.0]
        if last_second:
            ss_fb = sum(d['feedback'] for d in last_second) / len(last_second)
            ss_error = end - ss_fb
        else:
            ss_error = 0
        
        max_error = max(abs(d['error']) for d in data)
        
        return {
            'rise_time': rise_time,
            'settling_time': settling_time,
            'overshoot': overshoot,
            'ss_error': ss_error,
            'max_error': max_error,
        }
    
    def run_load_test(self):
        """Run interactive load recovery test (Guide §7.2)."""
        if not self._start_test("Load Recovery"):
            return
        threading.Thread(target=self._load_sequence, daemon=True).start()
    
    def _load_sequence(self):
        """Execute load recovery test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("LOAD RECOVERY TEST (Guide §7.2)")
        self.log_result("="*50)
        
        self.hal.send_mdi("M3 S1000")
        self.log_result("Stabilizing at 1000 RPM...")
        time.sleep(4)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        _, baseline_samples = self._sample_signal(MONITOR_PINS['feedback'], 1.0, 0.1)
        baseline = sum(baseline_samples) / len(baseline_samples) if baseline_samples else 1000
        
        self.log_result(f"Baseline: {baseline:.0f} RPM")
        self.log_result("\n>>> Apply load NOW (e.g., wood against chuck) <<<")
        self.log_result(">>> Hold for 3 seconds, then release <<<")
        
        min_rpm = baseline
        max_droop = 0
        droop_time = None
        
        samples = []
        start = time.time()
        
        while time.time() - start < 10.0:
            if self.test_abort:
                break
            
            fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
            samples.append((time.time() - start, fb))
            
            if fb < min_rpm:
                min_rpm = fb
                droop_time = time.time() - start
                max_droop = baseline - min_rpm
            
            time.sleep(0.1)
        
        recovery_time = None
        if droop_time:
            for t, fb in samples:
                if t > droop_time and abs(fb - baseline) < 20:
                    recovery_time = t - droop_time
                    break
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Baseline: {baseline:.0f} RPM")
        self.log_result(f"  Minimum during load: {min_rpm:.0f} RPM")
        self.log_result(f"  Max droop: {max_droop:.0f} RPM ({max_droop/baseline*100:.1f}%)")
        
        if recovery_time:
            self.log_result(f"  Recovery time: {recovery_time:.2f} s")
            self.log_result(f"\nASSESSMENT: {self._assess_recovery(recovery_time)}")
            
            if recovery_time > TARGETS.recovery_good:
                self.log_result("  → Consider increasing I-gain or MaxErrorI")
        else:
            self.log_result("  Recovery time: Did not recover within window")
            self.log_result("  → May need more I-gain for load disturbance rejection")
        
        self.log_result("\nSpindle still running - stop manually when ready")
        self.log_result("="*50)
        
        self._end_test()
    
    def run_steadystate_test(self):
        """Run steady-state/thermal monitor (Guide §7.3)."""
        if not self._start_test("Steady-State"):
            return
        
        try:
            duration = int(self.ss_duration.get())
        except ValueError:
            duration = 30
        
        duration = max(10, min(300, duration))
        
        threading.Thread(target=self._steadystate_sequence, args=(duration,),
                        daemon=True).start()
    
    def _steadystate_sequence(self, duration: int):
        """Execute steady-state monitoring."""
        self.log_result(f"\n{'='*50}")
        self.log_result(f"STEADY-STATE ACCURACY TEST ({duration}s) - Guide §7.3")
        self.log_result("="*50)
        
        self.hal.send_mdi("M3 S1000")
        self.log_result("Stabilizing at 1000 RPM...")
        time.sleep(4)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        self.log_result(f"Monitoring for {duration} seconds...")
        
        errors = []
        rpms = []
        integrators = []
        start = time.time()
        
        while time.time() - start < duration:
            if self.test_abort:
                break
            
            errors.append(self.hal.get_pin_value(MONITOR_PINS['error']))
            rpms.append(self.hal.get_pin_value(MONITOR_PINS['feedback']))
            integrators.append(self.hal.get_pin_value(MONITOR_PINS['errorI']))
            time.sleep(0.2)
        
        self.hal.send_mdi("M5")
        
        if not rpms or self.test_abort:
            self.log_result("  Test aborted or no data")
            self._end_test()
            return
        
        avg_rpm = sum(rpms) / len(rpms)
        rpm_min = min(rpms)
        rpm_max = max(rpms)
        rpm_range = rpm_max - rpm_min
        integrator_drift = integrators[-1] - integrators[0]
        ss_error = 1000.0 - avg_rpm
        
        variance = sum((r - avg_rpm) ** 2 for r in rpms) / len(rpms)
        std_dev = variance ** 0.5
        
        self.log_result(f"\nRESULTS:")
        self.log_result(f"  Average RPM: {avg_rpm:.1f}")
        self.log_result(f"  Std deviation: {std_dev:.2f} RPM")
        self.log_result(f"  Min/Max: {rpm_min:.1f} / {rpm_max:.1f} RPM")
        self.log_result(f"  Peak-to-peak: {rpm_range:.1f} RPM")
        self.log_result(f"  Steady-state error: {ss_error:.1f} RPM")
        self.log_result(f"  Integrator drift: {integrator_drift:+.1f}")
        
        self.log_result(f"\nASSESSMENT (Guide §7.4):")
        self.log_result(f"  SS Error: {self._assess_ss_error(ss_error)}")
        
        if rpm_range <= TARGETS.noise_excellent:
            self.log_result(f"  Stability: EXCELLENT (variation ≤{TARGETS.noise_excellent} RPM)")
        elif rpm_range <= TARGETS.noise_good:
            self.log_result(f"  Stability: GOOD (variation ≤{TARGETS.noise_good} RPM)")
        else:
            self.log_result(f"  Stability: HIGH VARIATION ({rpm_range:.0f} RPM)")
            self.log_result("    → Consider reducing P-gain")
        
        if abs(integrator_drift) > 20:
            self.log_result(f"\n  Note: Integrator drifted {integrator_drift:+.1f}")
            self.log_result("    (Normal - I-term compensating for motor heating)")
        
        self.log_result("="*50)
        self._end_test()
    
    # =========================================================================
    # ADVANCED TESTS
    # =========================================================================
    
    def run_decel_test(self):
        """Run deceleration test."""
        if not self._start_test("Deceleration"):
            return
        threading.Thread(target=self._decel_sequence, daemon=True).start()
    
    def _decel_sequence(self):
        """Execute deceleration test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("DECELERATION TEST: 1200 → 0 RPM")
        self.log_result("="*50)
        
        self.hal.send_mdi("M3 S1200")
        self.log_result("Accelerating to 1200 RPM...")
        time.sleep(3.5)
        
        if self.test_abort:
            self.hal.send_mdi("M5")
            self._end_test()
            return
        
        self.log_result("Stopping (M5)...")
        test_data = []
        start = time.time()
        self.hal.send_mdi("M5")
        
        while time.time() - start < 4.0:
            if self.test_abort:
                break
            
            t = time.time() - start
            fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
            test_data.append((t, fb))
            time.sleep(0.05)
        
        if not test_data:
            self._end_test()
            return
        
        stop_time = None
        for t, fb in test_data:
            if fb < 100:
                stop_time = t
                break
        
        if len(test_data) > 2:
            decel_rate = (test_data[0][1] - test_data[-1][1]) / (test_data[-1][0] - test_data[0][0])
        else:
            decel_rate = 0
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Time to <100 RPM: {stop_time:.2f} s" if stop_time else "  Did not stop in window")
        self.log_result(f"  Average decel rate: {decel_rate:.0f} RPM/s")
        
        rate_limit = self.hal.get_param('RateLimit')
        if rate_limit > 0 and abs(decel_rate - rate_limit) / rate_limit < 0.3:
            self.log_result(f"  ✓ Decel matches RATE_LIMIT ({rate_limit:.0f})")
        
        self.log_result("="*50)
        self._end_test()
    
    def run_ramp_test(self):
        """Run full ramp test."""
        if not self._start_test("Full Ramp"):
            return
        threading.Thread(target=self._ramp_sequence, daemon=True).start()
    
    def _ramp_sequence(self):
        """Execute full ramp test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("FULL RAMP TEST: 0 → 1800 → 0 RPM")
        self.log_result("="*50)
        
        test_data = []
        
        self.log_result("Ramping to 1800 RPM...")
        self.hal.send_mdi("M3 S1800")
        start = time.time()
        
        while time.time() - start < 4.0:
            if self.test_abort:
                break
            
            t = time.time() - start
            values = self.hal.get_all_values()
            test_data.append({
                'time': t,
                'phase': 'accel',
                'cmd': values.get('cmd_limited', 0),
                'feedback': values.get('feedback', 0),
            })
            time.sleep(0.1)
        
        self.log_result("Holding at 1800 RPM...")
        time.sleep(2.0)
        
        self.log_result("Ramping to 0 RPM...")
        self.hal.send_mdi("M5")
        decel_start = time.time()
        
        while time.time() - decel_start < 4.0:
            if self.test_abort:
                break
            
            t = time.time() - start
            values = self.hal.get_all_values()
            test_data.append({
                'time': t,
                'phase': 'decel',
                'cmd': values.get('cmd_limited', 0),
                'feedback': values.get('feedback', 0),
            })
            time.sleep(0.1)
        
        if not test_data:
            self._end_test()
            return
        
        max_fb = max(d['feedback'] for d in test_data)
        max_error = max(abs(d['cmd'] - d['feedback']) for d in test_data)
        
        self.log_result(f"\nResults:")
        self.log_result(f"  Peak feedback: {max_fb:.0f} RPM")
        self.log_result(f"  Max tracking error: {max_error:.0f} RPM")
        
        if max_error < 100:
            self.log_result("  ✓ Good tracking throughout ramp")
        else:
            self.log_result("  ⚠ Large tracking error - check rate limit settings")
        
        self.log_result("="*50)
        self._end_test()
    
    def run_full_suite(self):
        """Run abbreviated full test suite."""
        if not self._start_test("Full Suite"):
            return
        
        if not messagebox.askyesno("Full Test Suite",
                                   "This will run a sequence of tests:\n\n"
                                   "1. Signal Chain Check\n"
                                   "2. Open Loop Test\n"
                                   "3. Forward PID Test\n"
                                   "4. Step Response\n\n"
                                   "Total time: ~2 minutes\n\n"
                                   "Continue?"):
            self._end_test()
            return
        
        threading.Thread(target=self._full_suite_sequence, daemon=True).start()
    
    def _full_suite_sequence(self):
        """Execute full test suite."""
        self.log_result(f"\n{'='*50}")
        self.log_result("FULL TEST SUITE")
        self.log_result("="*50)
        
        tests = [
            ("Signal Chain", self._signal_chain_sequence),
            ("Open Loop", self._open_loop_sequence),
            ("Forward PID", self._forward_sequence),
        ]
        
        for name, func in tests:
            if self.test_abort:
                self.log_result(f"\n⏹ Suite aborted at {name}")
                break
            
            self.log_result(f"\n>>> Running {name} <<<")
            self.test_running = True
            func()
            time.sleep(1.0)
        
        if not self.test_abort:
            self.log_result(f"\n>>> Running Step Response <<<")
            self._step_sequence(500, 1200)
        
        self.log_result(f"\n{'='*50}")
        self.log_result("FULL SUITE COMPLETE")
        self.log_result("="*50)
        
        self._end_test()
    
    def reset_revs_counter(self):
        """Reset revolutions counter."""
        if hasattr(self.hal, '_mock_state'):
            self.hal._mock_state.revolutions = 0.0
        self.log_result("Revolutions counter reset.")
    
    # =========================================================================
    # FAULT TOGGLE METHODS (Mock Mode)
    # =========================================================================
    
    def toggle_encoder_fault(self):
        """Toggle encoder fault simulation."""
        if not self.hal.is_mock:
            return
        current = getattr(self.hal._mock_state, 'encoder_fault', False)
        self.hal.set_mock_fault('encoder', not current)
        state = "ON" if not current else "OFF"
        self.btn_enc_fault.config(text=f"Encoder Fault: {state}")
        self.log_result(f"[MOCK] Encoder fault: {state}")
    
    def toggle_polarity_fault(self):
        """Toggle polarity reversed simulation."""
        if not self.hal.is_mock:
            return
        current = getattr(self.hal._mock_state, 'polarity_reversed', False)
        self.hal.set_mock_fault('polarity', not current)
        state = "ON" if not current else "OFF"
        self.btn_polarity.config(text=f"Polarity Reversed: {state}")
        self.log_result(f"[MOCK] Polarity reversed: {state}")
    
    def toggle_dpll_fault(self):
        """Toggle DPLL disabled simulation."""
        if not self.hal.is_mock:
            return
        current = getattr(self.hal._mock_state, 'dpll_disabled', False)
        self.hal.set_mock_fault('dpll', not current)
        state = "ON" if not current else "OFF"
        self.btn_dpll.config(text=f"DPLL Disabled: {state}")
        self.log_result(f"[MOCK] DPLL disabled: {state}")
    
    def toggle_vfd_fault(self):
        """Toggle VFD fault simulation."""
        if not self.hal.is_mock:
            return
        current = getattr(self.hal._mock_state, 'vfd_fault', False)
        self.hal.set_mock_fault('vfd', not current)
        state = "ON" if not current else "OFF"
        self.btn_vfd_fault.config(text=f"VFD Fault: {state}")
        self.log_result(f"[MOCK] VFD fault: {state}")
    
    def toggle_estop(self):
        """Toggle E-stop simulation."""
        if not self.hal.is_mock:
            return
        current = getattr(self.hal._mock_state, 'estop_triggered', False)
        self.hal.set_mock_fault('estop', not current)
        state = "ON" if not current else "OFF"
        self.btn_estop.config(text=f"E-Stop: {state}")
        self.log_result(f"[MOCK] E-Stop: {state}")
    
    def run_mock_watchdog_test(self):
        """
        Run safe encoder watchdog test (Guide §6.6) - MOCK MODE ONLY.
        
        This test safely simulates an encoder fault to verify the watchdog
        would trigger. It uses programmatic fault injection rather than
        requiring physical cable disconnection.
        """
        if not self.hal.is_mock:
            messagebox.showinfo("Mock Only", 
                "This test only runs in mock mode for safety.\n\n"
                "On real hardware, encoder watchdog behavior should be\n"
                "verified during initial commissioning with the spindle\n"
                "stopped and proper safety procedures in place.")
            return
        
        if not self._start_test("Mock Watchdog"):
            return
        
        threading.Thread(target=self._mock_watchdog_sequence, daemon=True).start()
    
    def _mock_watchdog_sequence(self):
        """Execute safe mock watchdog test."""
        self.log_result(f"\n{'='*50}")
        self.log_result("ENCODER WATCHDOG TEST - MOCK MODE (Guide §6.6)")
        self.log_result("="*50)
        self.log_result("This is a SAFE simulation - no physical disconnection required.")
        
        # Start spindle in mock mode
        self.hal.send_mdi("M3 S1000")
        self.log_result("\nStarting spindle at 1000 RPM...")
        time.sleep(2)
        
        fb_before = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        self.log_result(f"Feedback before fault: {fb_before:.0f} RPM")
        
        # Inject encoder fault programmatically
        self.log_result("\nInjecting encoder fault via set_mock_fault()...")
        self.hal.set_mock_fault('encoder', True)
        time.sleep(1.5)
        
        # Check response
        fb_after = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        enc_fault = getattr(self.hal._mock_state, 'encoder_fault', False)
        estop = getattr(self.hal._mock_state, 'estop_triggered', False)
        
        self.log_result(f"\nFeedback after fault: {fb_after:.0f} RPM")
        self.log_result(f"Encoder fault flag: {'SET' if enc_fault else 'CLEAR'}")
        self.log_result(f"E-stop triggered: {'YES' if estop else 'NO'}")
        
        # Analysis
        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")
        
        if enc_fault:
            self.log_result("  ✓ Encoder fault was detected")
        else:
            self.log_result("  ✗ Encoder fault not detected")
        
        if fb_after < fb_before * 0.5 or estop:
            self.log_result("  ✓ Mock system responded to fault")
            self.log_result("\nIn a real system, this would trigger:")
            self.log_result("  - Watchdog timeout (encoder.00.watchdog)")
            self.log_result("  - External-OK signal drop")
            self.log_result("  - E-stop via safety chain")
        else:
            self.log_result("  ⚠ Mock system continued running")
            self.log_result("    (This tests the mock, not real watchdog)")
        
        # Clear fault and stop
        self.log_result("\nClearing fault and stopping...")
        self.hal.set_mock_fault('encoder', False)
        self.hal.send_mdi("M5")
        
        # Update button state if it exists
        if self.btn_enc_fault:
            self.btn_enc_fault.config(text="Encoder Fault: OFF")
        
        self.log_result("\n" + "="*50)
        self.log_result("MOCK WATCHDOG TEST COMPLETE")
        self.log_result("="*50)
        self.log_result("\nNote: Real watchdog testing should be done during")
        self.log_result("commissioning with spindle OFF and oscilloscope/")
        self.log_result("logic analyzer to verify timing.")
        
        self._end_test()


# =============================================================================
# CHECKLIST WIDGET
# =============================================================================

class ChecklistWidget(ttk.Frame):
    """Reusable checklist widget."""
    
    def __init__(self, parent, title: str, items: List[str], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.items = items
        self.vars = []
        
        ttk.Label(self, text=title, font=("Arial", 10, "bold")).pack(anchor="w")
        
        for item in items:
            var = tk.BooleanVar()
            self.vars.append(var)
            cb = ttk.Checkbutton(self, text=item, variable=var)
            cb.pack(anchor="w", padx=10)
    
    def get_completion(self) -> Tuple[int, int]:
        """Get (completed, total) counts."""
        completed = sum(1 for v in self.vars if v.get())
        return completed, len(self.vars)
    
    def is_complete(self) -> bool:
        """Check if all items are checked."""
        return all(v.get() for v in self.vars)
    
    def reset(self):
        """Uncheck all items."""
        for v in self.vars:
            v.set(False)


# =============================================================================
# CHECKLISTS TAB CLASS
# =============================================================================

class ChecklistsTab:
    """
    Checklists feature slice.
    
    Provides pre-flight and commissioning checklists from the tuning guide:
    - Hardware Checklist (§5 Pre-Flight Verification)
    - Commissioning Checklist (final verification before production use)
    """
    
    def __init__(self, parent: ttk.Frame):
        """
        Initialize checklists tab.
        
        Args:
            parent: Parent frame to build UI in
        """
        self.parent = parent
        self.hw_checklist = None
        self.comm_checklist = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the checklists UI."""
        # Header
        header = ttk.Frame(self.parent)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header, text="Pre-Flight & Commissioning Checklists",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Progress display
        self.progress_label = ttk.Label(header, text="Progress: 0/0", 
                                        font=("Arial", 10))
        self.progress_label.pack(side=tk.RIGHT)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.parent)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", 
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable area
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Hardware Checklist (§5 Pre-Flight)
        hw_frame = ttk.LabelFrame(scrollable, text="Hardware Checklist (Pre-Flight §5)", 
                                  padding="10")
        hw_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Extract descriptions from tuple list
        hw_items = [desc for _, desc in HARDWARE_CHECKLIST]
        self.hw_checklist = ChecklistWidget(hw_frame, "", hw_items)
        self.hw_checklist.pack(fill=tk.X)
        
        # Bind checkbuttons to update progress
        for var in self.hw_checklist.vars:
            var.trace_add("write", lambda *args: self._update_progress())
        
        # Hardware checklist buttons
        hw_btn_frame = ttk.Frame(hw_frame)
        hw_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(hw_btn_frame, text="Reset Hardware Checklist",
                  command=self._reset_hardware).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Commissioning Checklist
        comm_frame = ttk.LabelFrame(scrollable, text="Commissioning Checklist (Final Verification)", 
                                    padding="10")
        comm_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Extract descriptions from tuple list
        comm_items = [desc for _, desc in COMMISSIONING_CHECKLIST]
        self.comm_checklist = ChecklistWidget(comm_frame, "", comm_items)
        self.comm_checklist.pack(fill=tk.X)
        
        # Bind checkbuttons to update progress
        for var in self.comm_checklist.vars:
            var.trace_add("write", lambda *args: self._update_progress())
        
        # Commissioning checklist buttons
        comm_btn_frame = ttk.Frame(comm_frame)
        comm_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(comm_btn_frame, text="Reset Commissioning Checklist",
                  command=self._reset_commissioning).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Overall controls
        ctrl_frame = ttk.Frame(scrollable)
        ctrl_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Button(ctrl_frame, text="Reset All Checklists",
                  command=self._reset_all).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(ctrl_frame, text="", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Initial progress update
        self._update_progress()
    
    def _update_progress(self):
        """Update progress display."""
        hw_done, hw_total = self.hw_checklist.get_completion()
        comm_done, comm_total = self.comm_checklist.get_completion()
        
        total_done = hw_done + comm_done
        total_items = hw_total + comm_total
        
        self.progress_label.config(text=f"Progress: {total_done}/{total_items}")
        
        # Update status
        if total_done == total_items:
            self.status_label.config(text="✓ All checklists complete!", foreground="green")
        elif hw_done == hw_total:
            self.status_label.config(text="Hardware complete, commissioning pending", 
                                     foreground="blue")
        else:
            self.status_label.config(text="", foreground="blue")
    
    def _reset_hardware(self):
        """Reset hardware checklist."""
        self.hw_checklist.reset()
        self._update_progress()
    
    def _reset_commissioning(self):
        """Reset commissioning checklist."""
        self.comm_checklist.reset()
        self._update_progress()
    
    def _reset_all(self):
        """Reset all checklists."""
        self.hw_checklist.reset()
        self.comm_checklist.reset()
        self._update_progress()
    
    def is_hardware_complete(self) -> bool:
        """Check if hardware checklist is complete."""
        return self.hw_checklist.is_complete()
    
    def is_commissioning_complete(self) -> bool:
        """Check if commissioning checklist is complete."""
        return self.comm_checklist.is_complete()
    
    def is_all_complete(self) -> bool:
        """Check if all checklists are complete."""
        return self.is_hardware_complete() and self.is_commissioning_complete()
