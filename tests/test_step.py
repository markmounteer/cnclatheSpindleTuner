"""
Step Response Test (Guide §7.1)

Measures step response characteristics: settling time, overshoot, error.
"""

import time
import threading

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None
    _HAS_TKINTER = False

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription, TARGETS


class StepTest(BaseTest):
    """Step response test (Guide §7.1)."""

    TEST_NAME = "Step Response Test"
    GUIDE_REF = "Guide §7.1"

    def __init__(self, *args, step_from: int = 500, step_to: int = 1200, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_from = step_from
        self.step_to = step_to

    def set_step_values(self, step_from: int, step_to: int):
        """Set the step test parameters."""
        self.step_from = step_from
        self.step_to = step_to

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Step Response Test",
            guide_ref="§7.1",
            purpose="""
Measure the system's response to a speed step change.
Quantifies key performance metrics:

- Rise Time: Time to go from 10% to 90% of step
- Settling Time: Time to stay within 2% of target
- Overshoot: Peak excursion beyond target (%)
- Steady-State Error: Final offset from target

This is the primary test for evaluating tuning quality.""",

            prerequisites=[
                "Basic startup tests completed (§6)",
                "PID parameters at baseline or current tuning",
                "Spindle area clear",
            ],

            procedure=[
                "1. Set desired FROM and TO speeds in the UI",
                "2. Click 'Run Test' to begin",
                "3. Spindle stabilizes at FROM speed",
                "4. Speed stepped to TO speed",
                "5. Response sampled for 5 seconds",
                "6. Metrics calculated and assessed vs Guide §7.4",
            ],

            expected_results=[
                "Settling time: <2s EXCELLENT, <3s GOOD",
                "Overshoot: <5% EXCELLENT, <10% GOOD",
                "Steady-state error: <8 RPM EXCELLENT, <15 RPM GOOD",
                "No sustained oscillation after settling",
            ],

            troubleshooting=[
                "Slow settling (>3s):",
                "  -> Increase I-gain (if no oscillation)",
                "  -> Check rate limit not too slow",
                "High overshoot (>10%):",
                "  -> Verify limit2 is working",
                "  -> Reduce FF1 if immediate overshoot",
                "  -> Reduce I-gain if delayed overshoot",
                "Large steady-state error:",
                "  -> Increase I-gain or maxerrorI",
            ],

            safety_notes=[
                "Test runs between configured speeds",
                "Keep clear of spindle during test",
                "Spindle stops after test completes",
            ]
        )

    def run(self, step_from: int = None, step_to: int = None):
        """Start step test with optional speed parameters."""
        if step_from is not None:
            self.step_from = step_from
        if step_to is not None:
            self.step_to = step_to

        if self.step_from == self.step_to:
            messagebox.showerror("Error", "Start and end speeds must differ")
            return

        if not self.start_test():
            return

        threading.Thread(target=self._sequence, daemon=True).start()

    def _sequence(self):
        """Execute step response test."""
        start = self.step_from
        end = self.step_to

        self.log_header(f"STEP RESPONSE TEST: {start} -> {end} RPM")
        self.update_progress(0, f"Stabilizing at {start} RPM...")

        self.hal.send_mdi(f"M3 S{start}")
        self.log_result(f"Stabilizing at {start} RPM...")
        time.sleep(3)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        self.update_progress(20, f"Stepping to {end} RPM...")

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

            progress = 20 + (t / 5.0) * 60
            self.update_progress(progress, f"Sampling... {values.get('feedback', 0):.0f} RPM")

            time.sleep(0.1)

        self.hal.send_mdi("M5")
        self.update_progress(85, "Calculating metrics...")

        if not test_data or self.test_abort:
            self.log_result("  Test aborted or no data")
            self.end_test()
            return

        # Calculate metrics using base class method
        metrics = self.calculate_step_metrics(start, end, test_data)

        self.log_result(f"\nRESULTS:")
        self.log_result(f"  Rise time (10-90%): {metrics['rise_time']:.2f} s")
        self.log_result(f"  Settling time (2%): {metrics['settling_time']:.2f} s")
        self.log_result(f"  Overshoot: {metrics['overshoot']:.1f}%")
        self.log_result(f"  Steady-state error: {metrics['ss_error']:.1f} RPM")
        self.log_result(f"  Max error during step: {metrics['max_error']:.1f} RPM")

        self.log_result(f"\nASSESSMENT (Guide §7.4):")
        self.log_result(f"  Settling: {self.assess_settling(metrics['settling_time'])}")
        self.log_result(f"  Overshoot: {self.assess_overshoot(metrics['overshoot'])}")
        self.log_result(f"  SS Error: {self.assess_ss_error(metrics['ss_error'])}")

        self.update_progress(100, "Complete")

        if (metrics['settling_time'] <= TARGETS.settling_excellent and
                metrics['overshoot'] <= TARGETS.overshoot_excellent):
            self.log_footer("EXCELLENT")
            self.log_result("Fast settling, minimal overshoot")
        elif (metrics['settling_time'] <= TARGETS.settling_good and
              metrics['overshoot'] <= TARGETS.overshoot_good):
            self.log_footer("GOOD")
            self.log_result("Acceptable performance")
        else:
            self.log_footer("NEEDS TUNING")
            self.log_result("See troubleshooter for suggestions")

        self.end_test()
