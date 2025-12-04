#!/usr/bin/env python3
"""
Spindle Tuner - Troubleshooter Feature

Interactive diagnosis and system health monitoring based on
Spindle PID Tuning Guide v5.3.

Features:
- Live System Health Audit (compares current params to baseline)
- Interactive Diagnostic Wizard with back navigation
- "Apply Fix" automation for common tuning issues
- Searchable symptom reference library
- Reset to Baseline functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any

from config import SYMPTOM_DIAGNOSIS, BASELINE_PARAMS, TUNING_PARAMS


# =============================================================================
# DIAGNOSTIC LOGIC
# =============================================================================

class DiagnosticWizard:
    """
    Decision tree logic for the interactive wizard.
    
    Contains questions, diagnosis results, and automated fix actions.
    Tracks navigation history for back button support.
    """

    def __init__(self):
        self.history: List[str] = []
        self.current_node_id: str = "root"

    def start(self) -> Dict[str, Any]:
        """Start or restart the wizard."""
        self.history.clear()
        self.current_node_id = "root"
        return self._get_node("root")
    
    def step(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Move to a new node, tracking history."""
        node = self._get_node(node_id)
        if node:
            self.history.append(self.current_node_id)
            self.current_node_id = node_id
        return node
    
    def back(self) -> Optional[Dict[str, Any]]:
        """Go back to previous node."""
        if not self.history:
            return None
        prev_id = self.history.pop()
        self.current_node_id = prev_id
        return self._get_node(prev_id)
    
    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self.history) > 0
        
    def _get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Define the decision tree structure.
        
        Returns a dict representing a Question node or a Result node.
        
        Structure:
        - Question: {'question': str, 'options': [(label, next_node_id), ...]}
        - Result:   {'result': str, 'fix': str, 'color': str, 'actions': {param: value}}
        """
        nodes = {
            "root": {
                "question": "What is the primary behavior you are observing?",
                "options": [
                    ("Unstable Speed / Oscillation", "oscillation"),
                    ("Speed Accuracy / Error", "accuracy"),
                    ("Motion Behavior (Starts/Stops)", "motion"),
                    ("Hardware / VFD / Encoder", "hardware"),
                    ("Threading / Synchronization", "threading"),
                    ("Performance / Delays", "performance"),
                ]
            },
            
            # --- OSCILLATION BRANCH (§9) ---
            "oscillation": {
                "question": "Describe the oscillation frequency:",
                "options": [
                    ("Fast (>1 Hz, rapid vibration/noise)", "fast_osc"),
                    ("Slow (<1 Hz, rhythmic surging)", "slow_osc"),
                    ("Only happens at very low speed (<200 RPM)", "low_speed_hunt"),
                ]
            },
            "fast_osc": {
                "result": "Excessive P-Gain (VFD Delay)",
                "fix": "• VFDs have ~1.5s delay; high P-gain causes violent oscillation.\n• Action: Reduce P to 0.05 and increase Deadband.",
                "color": "red",
                "actions": {'P': 0.05, 'Deadband': 15.0}
            },
            "slow_osc": {
                "result": "VFD/PID Loop Fighting",
                "fix": "• Likely VFD 'Torque Boost' or 'Slip Comp' fighting PID I-term.\n• Manual: Set VFD P72=0 (Torque Boost).\n• Action: Reduce I-gain temporarily to stabilize.",
                "color": "orange",
                "actions": {'I': 0.5}
            },
            "low_speed_hunt": {
                "result": "Deadband Too Tight",
                "fix": "• At low speeds, encoder resolution limits accuracy.\n• Action: Relax Deadband to 20 RPM to stop hunting.\n• Check DPLL configuration and vel-timeout=0.1.",
                "color": "yellow",
                "actions": {'Deadband': 20.0}
            },
            
            # --- ACCURACY BRANCH (§9, §12) ---
            "accuracy": {
                "question": "What type of accuracy problem?",
                "options": [
                    ("Steady state error (>10 RPM off)", "ss_error"),
                    ("RPM drops significantly under load", "load_droop"),
                    ("Drift over time (hot vs cold)", "thermal_drift"),
                    ("Wrong speed scaling (too high/low)", "wrong_scaling"),
                    ("Speed reads 0 or wrong direction", "encoder_reading"),
                ]
            },
            "ss_error": {
                "result": "Insufficient Integral Gain",
                "fix": "• The I-term handles long-term error correction.\n• Action: Increase I-gain to 1.2.\n• Reduce Deadband if too high and check encoder scale=4096.",
                "color": "yellow",
                "actions": {'I': 1.2}
            },
            "load_droop": {
                "result": "Weak Load Rejection",
                "fix": "• Motor slip increases with load; PID must compensate.\n• Action: Increase MaxErrorI to allow more torque correction and I-gain.",
                "color": "orange",
                "actions": {'MaxErrorI': 80.0, 'I': 1.5}
            },
            "thermal_drift": {
                "result": "Thermal Slip Drift",
                "fix": "• Motor slip increases as it heats (2.7% cold → 3.6% hot).\n• Action: Increase I-gain and MaxErrorI to track drift.",
                "color": "yellow",
                "actions": {'I': 1.5, 'MaxErrorI': 80.0}
            },
            "wrong_scaling": {
                "result": "FF0 or VFD Scaling Error",
                "fix": "• FF0 must be 1.0 for voltage scaling.\n• Check VFD max freq >=62Hz.",
                "color": "red",
                "actions": {'FF0': 1.0}
            },
            "encoder_reading": {
                "result": "Encoder Configuration Issue",
                "fix": "• If negative RPM: Invert ENCODER_SCALE in INI.\n• If 0 RPM: Check physical wiring and Mesa jumpers (W10/W11).",
                "color": "red",
                "actions": None
            },

            # --- MOTION BRANCH (§9, §12) ---
            "motion": {
                "question": "When does the issue occur?",
                "options": [
                    ("Overshoot during speed changes", "overshoot"),
                    ("Undershoot or slow to reach speed", "slow_response"),
                    ("Spindle stalls or trips VFD", "stall"),
                    ("Runaway in Reverse (M4)", "runaway"),
                    ("Integrator windup (sustained error)", "integrator_windup"),
                ]
            },
            "overshoot": {
                "result": "Aggressive Feedforward / Rate Limit",
                "fix": "• Command is changing faster than VFD can respond.\n• Action: Reduce Accel Feedforward (FF1) and set Rate Limit.",
                "color": "yellow",
                "actions": {'FF1': 0.25, 'RateLimit': 1000.0}
            },
            "slow_response": {
                "result": "Weak Feedforward",
                "fix": "• Increase FF1 for better ramp tracking.\n• Check VFD accel time matches RateLimit.",
                "color": "yellow",
                "actions": {'FF1': 0.4}
            },
            "stall": {
                "result": "Torque/Current Limit Reached",
                "fix": "• VFD is hitting current limit or ramping too fast.\n• Manual: Increase VFD P0.11 (Accel Time).\n• Action: Reduce Rate Limit to match VFD.",
                "color": "red",
                "actions": {'RateLimit': 800.0}
            },
            "runaway": {
                "result": "Missing ABS Component (Critical)",
                "fix": "• PID needs positive feedback even in reverse.\n• Manual: Verify 'abs' component is linked to feedback in HAL.\n• THIS IS A SAFETY CRITICAL CONFIGURATION ISSUE.",
                "color": "red",
                "actions": None
            },
            "integrator_windup": {
                "result": "Integrator Windup",
                "fix": "• Reduce MaxErrorI to 50.\n• Verify limit2 is active and check for large sustained errors.",
                "color": "orange",
                "actions": {'MaxErrorI': 50.0}
            },

            # --- HARDWARE BRANCH (§12) ---
            "hardware": {
                "question": "Select the hardware symptom:",
                "options": [
                    ("No Spindle Movement", "no_movement"),
                    ("No Encoder Counts", "no_counts"),
                    ("VFD Faults (Er.XX)", "vfd_fault"),
                    ("Mesa Card LEDs", "mesa_leds"),
                ]
            },
            "no_movement": {
                "result": "Enable/Signal Chain Broken",
                "fix": "• Check spindle-enable signal (halshow).\n• Verify VFD P0.01=1 (Terminal Control).\n• Check analog scaling (0-10V).",
                "color": "red",
                "actions": None
            },
            "no_counts": {
                "result": "Encoder Signal Loss",
                "fix": "• Check 5V power at encoder connector.\n• Check Mesa Jumpers: W10, W11, W13 must be RIGHT (Diff).\n• Try filter=0 temporarily.",
                "color": "red",
                "actions": None
            },
            "vfd_fault": {
                "result": "VFD Parameter Mismatch",
                "fix": "• Check P0.04 (Max Hz) >= 65Hz.\n• Check P0.11 (Accel) >= 1.5s.\n• Check P72 (Torque Boost) = 0.",
                "color": "orange",
                "actions": None
            },
            "mesa_leds": {
                "result": "Status Information",
                "fix": "• Green = Solid (Power OK)\n• Red = Blinking (Watchdog OK)\n• If Red Solid: FPGA configuration failed (check power/cable).",
                "color": "green",
                "actions": None
            },

            # --- THREADING BRANCH (§10) ---
            "threading": {
                "question": "What threading problem?",
                "options": [
                    ("No Index Pulse", "no_index"),
                    ("At-Speed Not Asserting", "no_at_speed"),
                    ("Bad Threads (Loss of Sync)", "bad_threads"),
                ]
            },
            "no_index": {
                "result": "Index Configuration",
                "fix": "• Check encoder Z channel wiring.\n• Verify hm2 encoder counter-mode=0.",
                "color": "red",
                "actions": None
            },
            "no_at_speed": {
                "result": "Tolerance Too Tight",
                "fix": "• Set AT_SPEED_TOLERANCE = 20 RPM in INI.\n• Check Deadband not too tight.",
                "color": "orange",
                "actions": {'Deadband': 15.0}
            },
            "bad_threads": {
                "result": "Sync Loss During Cut",
                "fix": "• Check for oscillation or droop during cut.\n• Increase I-gain for better stiffness.",
                "color": "yellow",
                "actions": {'I': 1.5}
            },

            # --- PERFORMANCE BRANCH (§12) ---
            "performance": {
                "question": "What performance issue?",
                "options": [
                    ("Unexpected Realtime Delay", "realtime_delay"),
                    ("VFD Slow Ramp / Response", "vfd_ramp"),
                ]
            },
            "realtime_delay": {
                "result": "Realtime Delay",
                "fix": "• Run latency-histogram test.\n• Disable CPU frequency scaling.\n• Check for competing processes.\n• Consider isolcpus kernel parameter.",
                "color": "orange",
                "actions": None
            },
            "vfd_ramp": {
                "result": "VFD Ramp Mismatch",
                "fix": "• Match RateLimit to VFD accel/decel times.\n• Action: Set RateLimit to 1200 RPM/s.",
                "color": "yellow",
                "actions": {'RateLimit': 1200.0}
            },
        }
        return nodes.get(node_id)


# =============================================================================
# TROUBLESHOOTER TAB
# =============================================================================

class TroubleshooterTab:
    """
    Enhanced Troubleshooter UI with Parameter Audit and Interactive Wizard.
    """

    def __init__(self, parent: ttk.Frame, hal_interface):
        self.parent = parent
        self.hal = hal_interface
        self.wizard_logic = DiagnosticWizard()
        
        # Track symptom entries for filtering
        self._symptom_widgets: List[tk.Frame] = []
        self._symptom_data: List[tuple] = []
        
        self._setup_ui()

    def _setup_ui(self):
        """Build the main UI layout."""
        # Split into two panes: Audit/Wizard (Left) and Reference Library (Right)
        paned = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollable frames for each pane
        left_pane = self._create_scrollable_pane(paned)
        right_pane = self._create_scrollable_pane(paned)
        
        paned.add(left_pane['container'], weight=1)
        paned.add(right_pane['container'], weight=1)
        
        # --- LEFT PANE ---
        self._setup_health_audit(left_pane['frame'])
        self._setup_wizard(left_pane['frame'])
        
        # --- RIGHT PANE ---
        self._setup_reference_library(right_pane['frame'])
        self._setup_vfd_checklist(right_pane['frame'])
        self._setup_halcmd_reference(right_pane['frame'])
        self._setup_quick_reference(right_pane['frame'])
    
    def _create_scrollable_pane(self, parent) -> Dict[str, Any]:
        """Create a scrollable pane with mousewheel support."""
        container = ttk.Frame(parent)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        frame = ttk.Frame(canvas)
        
        frame.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        # Bind mousewheel to canvas and all children
        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel_linux)
            widget.bind("<Button-5>", _on_mousewheel_linux)
        
        _bind_mousewheel(canvas)
        _bind_mousewheel(frame)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return {'container': container, 'canvas': canvas, 'frame': frame,
                'bind_mousewheel': _bind_mousewheel}

    # =========================================================================
    # LEFT PANE: AUDIT & WIZARD
    # =========================================================================

    def _setup_health_audit(self, parent: ttk.Frame):
        """Setup live parameter health check."""
        frame = ttk.LabelFrame(parent, text="System Health Audit", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.audit_labels: Dict[str, tuple] = {}
        
        # Grid layout for audit items
        headers = ["Parameter", "Current", "Baseline", "Status"]
        for col, text in enumerate(headers):
            ttk.Label(frame, text=text, font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=col, sticky="w", padx=5, pady=2)
        
        audit_params = ['P', 'I', 'D', 'FF0', 'FF1', 'Deadband', 
                        'MaxErrorI', 'MaxCmdD', 'RateLimit', 'FilterGain']
        
        for row, param in enumerate(audit_params, 1):
            ttk.Label(frame, text=param).grid(row=row, column=0, sticky="w", padx=5)
            
            lbl_cur = ttk.Label(frame, text="--", width=8, font=("TkFixedFont", 10))
            lbl_cur.grid(row=row, column=1, sticky="w", padx=5)
            
            base_val = BASELINE_PARAMS.get(param, 0)
            ttk.Label(frame, text=f"{base_val}").grid(row=row, column=2, sticky="w", padx=5)
            
            lbl_stat = ttk.Label(frame, text="", width=25)
            lbl_stat.grid(row=row, column=3, sticky="w", padx=5)
            
            self.audit_labels[param] = (lbl_cur, lbl_stat)
        
        # Summary row
        summary_row = len(audit_params) + 1
        self.audit_summary = ttk.Label(frame, text="", font=("TkDefaultFont", 9, "italic"))
        self.audit_summary.grid(row=summary_row, column=0, columnspan=4, 
                                sticky="w", padx=5, pady=(5, 0))
        
        # Button row
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=summary_row + 1, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Run Audit", 
                   command=self._run_audit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to Baseline",
                   command=self._reset_to_baseline).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(frame, text="", foreground="gray")
        self.status_label.grid(row=summary_row + 2, column=0, columnspan=4, sticky="w", padx=5)
        
    def _run_audit(self):
        """Compare current HAL values against Guide v5.3 recommendations."""
        if not self.hal.is_connected and not self.hal.is_mock:
            self._show_status("Not connected to HAL")
            return

        warnings = 0
        
        for param, (lbl_cur, lbl_stat) in self.audit_labels.items():
            val = self.hal.get_param(param)
            lbl_cur.config(text=f"{val:.3f}")
            
            msg, color = self._audit_param(param, val)
            if msg != "OK":
                warnings += 1
            
            lbl_stat.config(text=msg, foreground=color)
        
        # Update summary
        if warnings == 0:
            self.audit_summary.config(text="All parameters within recommended ranges",
                                       foreground="green")
        else:
            self.audit_summary.config(text=f"{warnings} warning(s) detected - review above",
                                       foreground="orange")
        
        self._show_status("Audit complete")
    
    def _audit_param(self, param: str, val: float) -> tuple:
        """Audit a single parameter, returning (message, color)."""
        if param == 'P':
            if val > 0.3:
                return ("HIGH - VFD delay risk", "red")
            elif val < 0.01:
                return ("LOW - slow response", "orange")
        
        elif param == 'I':
            if val < 0.5:
                return ("LOW - weak stiffness", "orange")
            elif val > 3.0:
                return ("HIGH - windup risk", "orange")
        
        elif param == 'D':
            if val > 0.0:
                return ("Usually 0 - noise risk", "orange")
        
        elif param == 'FF0':
            if abs(val - 1.0) > 0.1:
                return ("Should be ~1.0", "red")
        
        elif param == 'FF1':
            if val > 0.5:
                return ("HIGH - overshoot risk", "orange")
            elif val < 0.3:
                return ("LOW - slow ramp", "gray")
        
        elif param == 'Deadband':
            if val < 5:
                return ("LOW - hunting risk", "orange")
        
        elif param == 'MaxErrorI':
            if val < 50:
                return ("LOW - slip limit", "orange")
        
        elif param == 'MaxCmdD':
            if val < 1000:
                return ("LOW - command limit", "gray")
        
        elif param == 'RateLimit':
            if val > 2000:
                return ("HIGH - VFD trip risk", "red")
            elif val < 800:
                return ("LOW - slow response", "gray")
        
        elif param == 'FilterGain':
            if val < 0.3:
                return ("LOW - noise risk", "gray")
        
        return ("OK", "green")
    
    def _reset_to_baseline(self):
        """Reset all parameters to baseline values."""
        if not self.hal.is_connected and not self.hal.is_mock:
            self._show_status("Not connected to HAL")
            return
        
        msg = "Reset all parameters to v5.3 baseline values?\n\n"
        for k, v in BASELINE_PARAMS.items():
            msg += f"  {k}: {v}\n"
        
        if not messagebox.askyesno("Reset to Baseline", msg):
            return
        
        success = True
        for param, value in BASELINE_PARAMS.items():
            if not self.hal.set_param(param, value):
                success = False
        
        if success:
            self._show_status("Parameters reset to baseline")
            self._run_audit()
        else:
            messagebox.showerror("Error", "Failed to set one or more parameters")

    def _setup_wizard(self, parent: ttk.Frame):
        """Setup interactive diagnostic wizard."""
        frame = ttk.LabelFrame(parent, text="Diagnostic Wizard", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.wiz_question = ttk.Label(frame, text="Welcome to the Diagnostic Wizard.", 
                                      font=("TkDefaultFont", 11, "bold"), wraplength=400)
        self.wiz_question.pack(fill=tk.X, pady=(0, 10))
        
        self.wiz_content_frame = ttk.Frame(frame)
        self.wiz_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Navigation
        nav_frame = ttk.Frame(frame)
        nav_frame.pack(fill=tk.X, pady=10)
        
        self.back_btn = ttk.Button(nav_frame, text="< Back", 
                                    command=self._wizard_back, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(nav_frame, text="Restart", 
                   command=self._restart_wizard).pack(side=tk.LEFT)
        
        self._restart_wizard()
        
    def _restart_wizard(self):
        """Reset wizard to start."""
        node = self.wizard_logic.start()
        self._render_node(node)
        self._update_back_button()
    
    def _wizard_back(self):
        """Go back one step in wizard."""
        node = self.wizard_logic.back()
        if node:
            self._render_node(node)
        self._update_back_button()
    
    def _update_back_button(self):
        """Enable/disable back button based on history."""
        if self.wizard_logic.can_go_back():
            self.back_btn.config(state=tk.NORMAL)
        else:
            self.back_btn.config(state=tk.DISABLED)
        
    def _render_node(self, node: Dict[str, Any]):
        """Render a wizard node (question or result)."""
        for widget in self.wiz_content_frame.winfo_children():
            widget.destroy()
            
        if "question" in node:
            self.wiz_question.config(text=node["question"], foreground="black")
            
            for i, (text, next_id) in enumerate(node["options"], 1):
                btn = ttk.Button(self.wiz_content_frame, text=f"{i}. {text}",
                                 command=lambda n=next_id: self._step_wizard(n))
                btn.pack(fill=tk.X, pady=2, ipady=3)
                
        elif "result" in node:
            color_map = {'red': '#c00000', 'orange': '#cc6600', 
                         'yellow': '#999900', 'green': '#008800'}
            color = color_map.get(node.get("color", "blue"), "blue")
            
            self.wiz_question.config(text=f"Diagnosis: {node['result']}", 
                                     foreground=color)
            
            sol_frame = ttk.LabelFrame(self.wiz_content_frame, text="Recommended Actions",
                                       padding=10)
            sol_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(sol_frame, text=node["fix"], justify=tk.LEFT,
                      wraplength=350).pack(anchor="w", pady=(0, 10))
            
            actions = node.get("actions")
            if actions:
                action_text = ", ".join([f"{k}={v}" for k, v in actions.items()])
                
                btn = ttk.Button(sol_frame, text=f"Apply Fix: {action_text}",
                                 command=lambda a=actions: self._apply_wizard_fix(a))
                btn.pack(fill=tk.X, pady=5)
            else:
                ttk.Label(sol_frame, text="(Manual configuration required)", 
                          foreground="gray").pack()

    def _step_wizard(self, node_id: str):
        """Move to next step in wizard."""
        node = self.wizard_logic.step(node_id)
        if node:
            self._render_node(node)
        self._update_back_button()
            
    def _apply_wizard_fix(self, actions: Dict[str, float]):
        """Apply the suggested fixes to HAL."""
        if not self.hal.is_connected and not self.hal.is_mock:
            messagebox.showerror("Error", "Not connected to HAL.")
            return
            
        msg = "Apply the following parameter changes?\n\n"
        for k, v in actions.items():
            msg += f"  {k}: {v}\n"
            
        if messagebox.askyesno("Apply Fix", msg):
            success = True
            for param, value in actions.items():
                if not self.hal.set_param(param, value):
                    success = False
            
            if success:
                messagebox.showinfo("Success", "Parameters updated successfully.")
                self._run_audit()
            else:
                messagebox.showerror("Error", "Failed to set one or more parameters.")

    def _show_status(self, msg: str):
        """Show status message."""
        self.status_label.config(text=msg)
        # Auto-clear after 5 seconds
        self.parent.after(5000, lambda: self.status_label.config(text=""))

    # =========================================================================
    # RIGHT PANE: REFERENCE LIBRARY
    # =========================================================================

    def _setup_reference_library(self, parent: ttk.Frame):
        """Setup searchable list of all symptoms."""
        frame = ttk.LabelFrame(parent, text="Symptom Library", padding="5")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search bar
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_symptoms())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(search_frame, text="Clear", width=6,
                   command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=(5, 0))
        
        # Severity legend
        legend_frame = ttk.Frame(frame)
        legend_frame.pack(fill=tk.X, pady=(0, 5))
        
        for color, label in [('#ffcccc', 'Critical'), ('#ffe6cc', 'Warning'), 
                             ('#ffffcc', 'Info')]:
            lbl = tk.Label(legend_frame, text=f" {label} ", bg=color, 
                           font=("TkDefaultFont", 8))
            lbl.pack(side=tk.LEFT, padx=2)
        
        # Scrollable symptom list
        list_container = ttk.Frame(frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.symptom_list_frame = ttk.Frame(canvas)
        
        self.symptom_list_frame.bind("<Configure>",
                                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.symptom_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel_linux)
        canvas.bind("<Button-5>", _on_mousewheel_linux)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate from SYMPTOM_DIAGNOSIS
        self._symptom_widgets.clear()
        self._symptom_data.clear()
        
        for title, solution, color in SYMPTOM_DIAGNOSIS:
            widget = self._create_symptom_entry(self.symptom_list_frame, title, solution, color)
            self._symptom_widgets.append(widget)
            self._symptom_data.append((title, solution, color))
    
    def _filter_symptoms(self):
        """Filter symptom library based on search text."""
        search_text = self.search_var.get().lower()
        
        for widget, (title, solution, _) in zip(self._symptom_widgets, self._symptom_data):
            if not search_text:
                widget.pack(fill=tk.X, pady=2, padx=2)
            elif search_text in title.lower() or search_text in solution.lower():
                widget.pack(fill=tk.X, pady=2, padx=2)
            else:
                widget.pack_forget()
            
    def _create_symptom_entry(self, parent, title: str, solution: str, color: str) -> tk.Frame:
        """Create a symptom entry widget."""
        color_hex = {
            'red': '#ffcccc',
            'orange': '#ffe6cc',
            'yellow': '#ffffcc',
            'green': '#ccffcc'
        }.get(color, '#ffffff')
        
        item = tk.Frame(parent, borderwidth=1, relief="solid", bg="white")
        
        header = tk.Frame(item, bg=color_hex, height=25)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title, bg=color_hex, 
                 font=("TkDefaultFont", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        content = tk.Frame(item, bg="white", padx=5, pady=5)
        content.pack(fill=tk.X)
        
        tk.Label(content, text=solution, justify=tk.LEFT, bg="white", 
                 wraplength=380).pack(anchor="w")
        
        item.pack(fill=tk.X, pady=2, padx=2)
        return item

    def _setup_vfd_checklist(self, parent: ttk.Frame):
        """Setup VFD parameter reference."""
        frame = ttk.LabelFrame(parent, text="VFD Configuration (XSY-AT1)", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        items = [
            ("P0.00", "50/60Hz", "Grid Frequency"),
            ("P0.04", "65-70Hz", "Max Frequency (Headroom)"),
            ("P0.11", "1.5 - 3.0s", "Accel Time (Match RateLimit)"),
            ("P0.12", "1.5 - 3.0s", "Decel Time"),
            ("P72", "0", "Torque Boost (MUST BE 0)"),
        ]
        
        for code, val, desc in items:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=code, font=("TkFixedFont", 10, "bold"), 
                      width=6).pack(side=tk.LEFT)
            ttk.Label(row, text=val, foreground="blue", width=12).pack(side=tk.LEFT)
            ttk.Label(row, text=desc).pack(side=tk.LEFT)
            
        ttk.Label(frame, text="Note: P72>0 causes slow oscillation!", 
                  foreground="red", font=("TkDefaultFont", 8, "italic")).pack(pady=(5, 0))

    def _setup_halcmd_reference(self, parent: ttk.Frame):
        """Setup halcmd quick reference."""
        frame = ttk.LabelFrame(parent, text="Halcmd Quick Reference", padding="10")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        commands = [
            ("Tuning", "halcmd setp pid.s.Igain 1.2"),
            ("Monitor", "halcmd show pin pid.s.error"),
            ("Safety", "halcmd show sig external-ok"),
        ]
        
        for title, cmd in commands:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=title, font=("TkDefaultFont", 9, "bold"), 
                      width=8).pack(side=tk.LEFT, padx=5)
            ttk.Label(row, text=cmd, font=("TkFixedFont", 9)).pack(side=tk.LEFT, padx=5)

    def _setup_quick_reference(self, parent: ttk.Frame):
        """Setup quick reference panel."""
        ref_frame = ttk.LabelFrame(parent, text="v5.3 Baseline Reference", padding="10")
        ref_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Two-column layout
        left_frame = ttk.Frame(ref_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(ref_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        params = list(BASELINE_PARAMS.items())
        mid = len(params) // 2
        
        for i, (param, value) in enumerate(params):
            target = left_frame if i < mid else right_frame
            text = f"{param}: {value}"
            ttk.Label(target, text=text, font=("TkFixedFont", 10)).pack(anchor=tk.W)
        
        # Tuning flowchart
        flow_frame = ttk.LabelFrame(parent, text="Tuning Flowchart", padding="10")
        flow_frame.pack(fill=tk.X, padx=5, pady=5)
        
        flowchart = """Unstable? ─┬─ Fast oscillation ──→ Reduce P, increase Deadband
           │
           ├─ Slow oscillation ──→ Disable VFD P72
           │
           └─ Stable ─┬─ Not reaching target ──→ Check VFD, MaxErrorI
                      ├─ Load causes droop ────→ Increase I-gain
                      ├─ Overshoot ─────────────→ Check limit2, reduce FF1
                      └─ All good ──────────────→ TUNING COMPLETE"""
        
        ttk.Label(flow_frame, text=flowchart, font=("TkFixedFont", 9),
                  justify=tk.LEFT).pack(anchor=tk.W)
        
        # Key principles
        principles_frame = ttk.LabelFrame(parent, text="Key Tuning Principles", padding="10")
        principles_frame.pack(fill=tk.X, padx=5, pady=5)
        
        principles = [
            "1. FF0 provides ~95% of control (must be 1.0)",
            "2. limit2.maxv = 1200 RPM/s prevents overshoot",
            "3. P-gain limited by VFD delay (~1.5s): keep 0.1-0.3",
            "4. I-gain compensates motor slip: 1.0-1.5",
            "5. Deadband prevents hunting: 10-15 RPM",
        ]
        
        for principle in principles:
            ttk.Label(principles_frame, text=principle, 
                      justify=tk.LEFT).pack(anchor=tk.W, pady=1)
