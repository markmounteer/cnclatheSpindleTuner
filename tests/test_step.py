"""
Step Response Test (Guide §7.1)

Measures step response characteristics: settling time, overshoot, error.
"""

import time
from typing import List, Dict, Optional

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None
    _HAS_TKINTER = False

from tests.base import BaseTest, TestDescription, TARGETS


class StepTest(BaseTest):
    """Step response test (Guide §7.1)."""

    TEST_NAME = "Step Response Test"
    GUIDE_REF = "Guide §7.1"

    # Test configuration constants
    SAMPLE_INTERVAL_S = 0.05  # 20Hz sampling for good step response resolution
    TEST_DURATION_S = 5.0     # Duration to sample after step
    STABILIZE_TIMEOUT_S = 10.0  # Max time to wait for stabilization
    STABILIZE_TOLERANCE_RPM = 10.0  # RPM tolerance for stabilization

    def __init__(self, *args, step_from: int = 500, step_to: int = 1200, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_from = step_from
        self.step_to = step_to

    def set_step_values(self, step_from: int, step_to: int) -> None:
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
                f"5. Response sampled for {cls.TEST_DURATION_S:.0f} seconds",
                "6. Metrics calculated and assessed vs Guide §7.4",
            ],

            expected_results=[
                f"Settling time: <{TARGETS.settling_excellent}s EXCELLENT, "
                f"<{TARGETS.settling_good}s GOOD",
                f"Overshoot: <{TARGETS.overshoot_excellent}% EXCELLENT, "
                f"<{TARGETS.overshoot_good}% GOOD",
                f"Steady-state error: <{TARGETS.ss_error_excellent} RPM EXCELLENT, "
                f"<{TARGETS.ss_error_good} RPM GOOD",
                "No sustained oscillation after settling",
            ],

            troubleshooting=[
                f"Slow settling (>{TARGETS.settling_good}s):",
                "  -> Increase I-gain (if no oscillation)",
                "  -> Check rate limit not too slow",
                f"High overshoot (>{TARGETS.overshoot_good}%):",
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

    def run(self, step_from: Optional[int] = None, step_to: Optional[int] = None) -> None:
        """Start step test with optional speed parameters."""
        if step_from is not None:
            self.step_from = step_from
        if step_to is not None:
            self.step_to = step_to

        if self.step_from == self.step_to:
            error_msg = "Start and end speeds must differ"
            if _HAS_TKINTER and messagebox is not None:
                messagebox.showerror("Error", error_msg)
            self.log_result(f"Error: {error_msg}")
            return

        if not self.start_test():
            return

        self.run_sequence(self._sequence)

    def _stabilize(
        self,
        target: int,
        timeout: Optional[float] = None,
        tolerance: Optional[float] = None,
    ) -> bool:
        """
        Wait for spindle to stabilize at target speed.

        Args:
            target: Target RPM to stabilize at
            timeout: Max seconds to wait (default: STABILIZE_TIMEOUT_S)
            tolerance: RPM tolerance for stabilization (default: STABILIZE_TOLERANCE_RPM)

        Returns:
            True if stabilized within timeout, False otherwise
        """
        if timeout is None:
            timeout = self.STABILIZE_TIMEOUT_S
        if tolerance is None:
            tolerance = self.STABILIZE_TOLERANCE_RPM

        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            if self.test_abort:
                return False

            values = self.hal.get_all_values()
            feedback = values.get('feedback', 0)

            if abs(feedback - target) < tolerance:
                return True

            time.sleep(0.1)

        return False

    def _sequence(self) -> None:
        """Execute step response test."""
        start = self.step_from
        end = self.step_to

        self.log_header(f"STEP RESPONSE TEST: {start} -> {end} RPM")
        self.update_progress(0, f"Stabilizing at {start} RPM...")

        # Phase 1: Stabilize at starting speed
        self.hal.send_mdi(f"M3 S{start}")
        self.log_result(f"Stabilizing at {start} RPM...")

        if not self._stabilize(start):
            if self.test_abort:
                self.log_result("Test aborted during stabilization")
            else:
                self.log_result("Failed to stabilize at start speed within timeout")
            self.hal.send_mdi("M5")
            return

        if self.test_abort:
            self.hal.send_mdi("M5")
            return

        # Phase 2: Execute step and collect data
        self.update_progress(20, f"Stepping to {end} RPM...")
        test_data: List[Dict[str, float]] = []
        self.log_result(f"Stepping to {end} RPM...")

        step_time = time.monotonic()
        self.hal.send_mdi(f"M3 S{end}")

        while time.monotonic() - step_time < self.TEST_DURATION_S:
            if self.test_abort:
                break

            t = time.monotonic() - step_time
            values = self.hal.get_all_values()

            sample = {
                'time': t,
                'cmd': values.get('cmd_limited', 0),
                'feedback': values.get('feedback', 0),
                'error': values.get('error', 0),
                'errorI': values.get('errorI', 0),
            }
            test_data.append(sample)

            progress = 20 + (t / self.TEST_DURATION_S) * 60
            self.update_progress(progress, f"Sampling... {values.get('feedback', 0):.0f} RPM")

            time.sleep(self.SAMPLE_INTERVAL_S)

        self.hal.send_mdi("M5")
        self.update_progress(85, "Calculating metrics...")

        if not test_data or self.test_abort:
            self.log_result("Test aborted or no data collected")
            return

        # Log collected data to data logger
        self.logger.log_samples(test_data)

        # Phase 3: Calculate and report metrics
        metrics = self.calculate_step_metrics(start, end, test_data)

        self.log_result("\nRESULTS:")
        self.log_result(f"  Rise time (10-90%): {metrics.rise_time_s:.2f} s")
        self.log_result(f"  Settling time (2%): {metrics.settling_time_s:.2f} s")
        self.log_result(f"  Overshoot: {metrics.overshoot_pct:.1f}%")
        self.log_result(f"  Steady-state error: {metrics.steady_state_error:.1f} RPM")
        self.log_result(f"  Max error during step: {metrics.max_error:.1f} RPM")

        self.log_result("\nASSESSMENT (Guide §7.4):")
        self.log_result(f"  Settling: {self.assess_settling(metrics.settling_time_s)}")
        self.log_result(f"  Overshoot: {self.assess_overshoot(metrics.overshoot_pct)}")
        self.log_result(f"  SS Error: {self.assess_ss_error(metrics.steady_state_error)}")

        self.update_progress(100, "Complete")

        # Determine overall result
        if (metrics.settling_time_s <= TARGETS.settling_excellent and
                metrics.overshoot_pct <= TARGETS.overshoot_excellent):
            self.log_footer("EXCELLENT")
            self.log_result("Fast settling, minimal overshoot")
        elif (metrics.settling_time_s <= TARGETS.settling_good and
              metrics.overshoot_pct <= TARGETS.overshoot_good):
            self.log_footer("GOOD")
            self.log_result("Acceptable performance")
        else:
            self.log_footer("NEEDS TUNING")
            self.log_result("See troubleshooter for suggestions")
