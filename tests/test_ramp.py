"""
Full Ramp Test

Tests complete 0->1800->0 RPM cycle.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription


class RampTest(BaseTest):
    """Full ramp test (0->max->0)."""

    TEST_NAME = "Full Ramp Test"
    GUIDE_REF = ""

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Full Ramp Test",
            guide_ref="",
            purpose="""
Test the complete speed range from 0 to maximum (1800 RPM)
and back to 0. This stress-tests the entire control system
including:

- Acceleration tracking
- Maximum speed stability
- Deceleration behavior
- Overall tracking error throughout

Use this to verify tuning across the full operating range.""",

            prerequisites=[
                "All basic tests completed",
                "Tuning stable at lower speeds",
                "VFD and motor rated for 1800 RPM",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle ramps from 0 to 1800 RPM",
                "3. Holds briefly at maximum speed",
                "4. Ramps back down to 0 RPM",
                "5. Tracking error monitored throughout",
            ],

            expected_results=[
                "Smooth acceleration and deceleration",
                "Peak speed reaches ~1800 RPM",
                "Max tracking error <100 RPM during ramps",
                "No oscillation at any speed",
            ],

            troubleshooting=[
                "Large tracking error during accel:",
                "  -> Increase FF1 for better prediction",
                "  -> Check RATE_LIMIT matches VFD",
                "Oscillation at high speed:",
                "  -> May need different tuning above 1500 RPM",
                "VFD trips:",
                "  -> Check VFD max frequency (P0.04)",
                "  -> Increase VFD accel time if needed",
            ],

            safety_notes=[
                "Test runs at MAXIMUM speed (1800 RPM)",
                "Ensure spindle is balanced",
                "Keep clear during test",
            ]
        )

    def run(self):
        """Start full ramp test in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute full ramp test."""
        self.log_header("FULL RAMP TEST: 0 -> 1800 -> 0 RPM")
        self.update_progress(0, "Starting ramp to 1800 RPM...")

        test_data = []

        self.log_result("Ramping to 1800 RPM...")
        self.hal.send_mdi("M3 S1800")
        start = time.time()

        # Acceleration phase
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

            progress = (t / 4.0) * 30
            self.update_progress(progress, f"Accelerating... {values.get('feedback', 0):.0f} RPM")

            time.sleep(0.1)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        # Hold at max
        self.log_result("Holding at 1800 RPM...")
        self.update_progress(35, "Holding at max speed...")
        time.sleep(2.0)

        # Deceleration phase
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

            decel_t = time.time() - decel_start
            progress = 40 + (decel_t / 4.0) * 50
            self.update_progress(progress, f"Decelerating... {values.get('feedback', 0):.0f} RPM")

            time.sleep(0.1)

        self.update_progress(95, "Analyzing results...")

        if not test_data:
            self.end_test()
            return

        max_fb = max(d['feedback'] for d in test_data)
        max_error = max(abs(d['cmd'] - d['feedback']) for d in test_data)

        self.log_result(f"\nResults:")
        self.log_result(f"  Peak feedback: {max_fb:.0f} RPM")
        self.log_result(f"  Max tracking error: {max_error:.0f} RPM")

        self.update_progress(100, "Complete")

        if max_error < 100:
            self.log_footer("PASS")
            self.log_result("  Good tracking throughout ramp")
        else:
            self.log_footer("TRACKING ERROR")
            self.log_result("  Large tracking error - check rate limit settings")

        self.end_test()
