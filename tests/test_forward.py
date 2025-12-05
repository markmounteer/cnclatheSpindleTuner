"""
Forward PID Test (Guide §6.2)

Verifies forward (M3) spindle operation with PID active.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription


class ForwardTest(BaseTest):
    """Forward PID test (Guide §6.2)."""

    TEST_NAME = "Forward PID Test"
    GUIDE_REF = "Guide §6.2"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Forward PID Test",
            guide_ref="§6.2",
            purpose="""
Test forward (M3) spindle operation with full PID control active.
This verifies that the closed-loop system achieves target speed,
the at-speed indicator works, and steady-state error is acceptable.

Run this test after open-loop check to confirm PID is working.""",

            prerequisites=[
                "Open Loop Check completed successfully",
                "PID parameters restored to baseline",
                "LinuxCNC loaded and machine power ON",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle started forward at 1000 RPM (M3 S1000)",
                "3. Wait 4 seconds for settling",
                "4. Feedback, error, and at-speed sampled",
                "5. Analyze if target reached with acceptable error",
            ],

            expected_results=[
                "Feedback reaches ~1000 RPM (within 10%)",
                "At-speed indicator becomes TRUE",
                "Steady-state error < 20 RPM",
                "Integrator shows slip compensation value",
            ],

            troubleshooting=[
                "Speed low: Check I-gain and maxerrorI limits",
                "No at-speed: Adjust AT_SPEED_TOLERANCE in INI",
                "Large error: Increase I-gain or check FF0",
                "Oscillation: Reduce P-gain (see Guide §9.1)",
            ],

            safety_notes=[
                "Test runs at 1000 RPM",
                "Forward rotation (M3)",
                "Spindle stops after test",
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
        self.update_progress(0, "Starting spindle forward...")

        self.hal.send_mdi("M3 S1000")
        self.log_result("Starting M3 S1000...")
        self.update_progress(10, "Accelerating...")

        time.sleep(4)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        self.update_progress(50, "Sampling feedback...")

        _, fb_samples = self.sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
        _, err_samples = self.sample_signal(MONITOR_PINS['error'], 1.0, 0.1)

        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])
        errorI = self.hal.get_pin_value(MONITOR_PINS['errorI'])

        self.hal.send_mdi("M5")
        self.update_progress(80, "Analyzing results...")

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
        self.log_result(f"  Feedback: {fb_avg:.1f} RPM (noise: +/-{fb_noise/2:.1f})")
        self.log_result(f"  Steady-state error: {err_avg:.1f} RPM")
        self.log_result(f"  Integrator: {errorI:.1f}")
        self.log_result(f"  At-speed: {'YES' if at_speed > 0.5 else 'NO'}")

        all_ok = True

        if fb_avg > 900:
            self.log_result("\n[OK] Speed reached target")
        else:
            self.log_result(f"\n[FAIL] Speed low: {fb_avg:.0f} RPM (expected ~1000)")
            all_ok = False

        if at_speed > 0.5:
            self.log_result("[OK] At-speed signal active")
        else:
            self.log_result("[WARN] At-speed signal not active")
            all_ok = False

        if abs(err_avg) < 20:
            self.log_result(f"[OK] Error small: {err_avg:.1f} RPM")
        else:
            self.log_result(f"[WARN] Error large: {err_avg:.1f} RPM")

        self.update_progress(100, "Complete")

        if all_ok:
            self.log_footer("PASS")
        else:
            self.log_footer("ISSUES DETECTED")

        self.end_test()
