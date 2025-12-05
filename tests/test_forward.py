"""
Forward PID Test (Guide §6.2)

Verifies forward (M3) spindle operation with PID active.
Checks for target accuracy, stability (jitter), and at-speed signal.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, ProcedureDescription


class ForwardTest(BaseTest):
    """Forward PID test (Guide §6.2)."""

    TEST_NAME = "Forward PID Test"
    GUIDE_REF = "Guide §6.2"

    # Configuration
    TARGET_RPM = 1000
    SETTLE_TIME = 4.0        # Seconds to wait before sampling
    SAMPLE_WINDOW = 2.0      # Duration of sampling
    TOLERANCE_RPM = 20       # Allow +/- 20 RPM error (2%)
    MAX_JITTER = 15.0        # Max allowed standard deviation

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Forward PID Test",
            guide_ref="§6.2",
            purpose="""
Test forward (M3) spindle operation with full PID control active.
This verifies that the closed-loop system achieves target speed,
the at-speed indicator works, and steady-state error is minimal.

It calculates Standard Deviation to detect PID oscillation.""",

            prerequisites=[
                "Open Loop Check completed successfully",
                "PID parameters restored to baseline",
                "LinuxCNC loaded and machine power ON",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                f"2. Spindle commands forward to {cls.TARGET_RPM} RPM",
                f"3. Wait {cls.SETTLE_TIME}s for settling",
                "4. Feedback, error, and stability sampled",
                "5. Stop spindle and analyze performance",
            ],

            expected_results=[
                f"RPM within {cls.TOLERANCE_RPM} RPM of target",
                f"Stability (StdDev) < {cls.MAX_JITTER}",
                "At-speed indicator becomes TRUE",
                "Steady-state error close to 0",
            ],

            troubleshooting=[
                "Speed low/high: Check P-gain or max output scaling",
                "Oscillation (High StdDev): Reduce P-gain, check D-gain",
                "Slow to settle: Increase I-gain",
                "No At-speed: Adjust AT_SPEED_TOLERANCE in INI file",
            ],

            safety_notes=[
                f"Test runs at {cls.TARGET_RPM} RPM",
                "Forward rotation (M3)",
                "Ensure chuck key is removed",
            ]
        )

    def run(self):
        """Start forward PID test in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute forward PID test."""
        self.log_header()
        
        # 1. Start Spindle
        self.update_progress(0, f"Commanding M3 S{self.TARGET_RPM}...")
        self.hal.send_mdi(f"M3 S{self.TARGET_RPM}")
        self.log_result(f"Command: M3 S{self.TARGET_RPM}")
        
        # 2. Wait for settling (with abort check)
        start_wait = time.time()
        while time.time() - start_wait < self.SETTLE_TIME:
            elapsed = time.time() - start_wait
            progress = 10 + (elapsed / self.SETTLE_TIME * 40) # Scale 10-50%
            self.update_progress(progress, "Accelerating & Settling...")
            
            if self.test_abort:
                self.hal.send_mdi("M5")
                self.end_test()
                return
            time.sleep(0.1)

        # 3. Sampling Phase
        self.update_progress(50, "Sampling feedback stability...")
        
        # Sample feedback and error pins
        _, fb_samples = self.sample_signal(MONITOR_PINS['feedback'], self.SAMPLE_WINDOW, 0.05)
        _, err_samples = self.sample_signal(MONITOR_PINS['error'], self.SAMPLE_WINDOW, 0.05)

        # Snapshot instantaneous pins
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])
        errorI = self.hal.get_pin_value(MONITOR_PINS['errorI'])

        # 4. Stop Spindle
        self.hal.send_mdi("M5")
        self.update_progress(80, "Analyzing results...")

        # 5. Data Analysis
        if not fb_samples:
            self.log_result("[ERROR] No data collected.")
            self.end_test()
            return

        # Calculate Statistics
        fb_avg = statistics.mean(fb_samples)
        fb_min = min(fb_samples)
        fb_max = max(fb_samples)
        # Use stdev if >1 sample, else 0
        fb_stdev = statistics.stdev(fb_samples) if len(fb_samples) > 1 else 0
        
        # 6. Reporting
        self.log_result("\n--- Analysis ---")
        self.log_result(f"Target: {self.TARGET_RPM} RPM")
        self.log_result(f"Actual Average: {fb_avg:.1f} RPM")
        self.log_result(f"Range: {fb_min:.0f} to {fb_max:.0f} RPM")
        self.log_result(f"Stability (StdDev): {fb_stdev:.2f} (Lower is better)")
        self.log_result(f"Integrator (I-term): {errorI:.1f}")
        self.log_result(f"At-Speed Signal: {'TRUE' if at_speed > 0.5 else 'FALSE'}")

        # 7. Pass/Fail Logic
        issues = []

        # Check 1: Accuracy (Steady State Error)
        if abs(self.TARGET_RPM - fb_avg) > self.TOLERANCE_RPM:
            issues.append(f"Accuracy Fail: Off by {abs(self.TARGET_RPM - fb_avg):.1f} RPM")
            self.log_result(f"[FAIL] Average RPM outside tolerance (+/-{self.TOLERANCE_RPM})")
        else:
            self.log_result("[PASS] Accuracy within tolerance")

        # Check 2: Stability (Oscillation)
        if fb_stdev > self.MAX_JITTER:
            issues.append("Stability Fail: Spindle oscillating")
            self.log_result(f"[FAIL] High Jitter/Oscillation (StdDev: {fb_stdev:.1f})")
            self.log_result("       -> Check P-gain (too high?) or belt tension")
        else:
            self.log_result("[PASS] Stability acceptable")

        # Check 3: At-Speed Signal
        if at_speed < 0.5:
            issues.append("Signal Fail: at-speed pin false")
            self.log_result("[FAIL] LinuxCNC did not report 'at-speed'")
        else:
            self.log_result("[PASS] 'at-speed' signal received")

        self.update_progress(100, "Complete")

        if not issues:
            self.log_footer("PASS")
        else:
            self.log_footer(f"FAIL ({len(issues)} issues)")

        self.end_test()
