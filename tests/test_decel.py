"""
Deceleration Test

Measures spindle deceleration behavior and rate.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription


class DecelTest(BaseTest):
    """Deceleration test."""

    TEST_NAME = "Deceleration Test"
    GUIDE_REF = ""

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Deceleration Test",
            guide_ref="",
            purpose="""
Measure the spindle's deceleration behavior when stopping.
Verifies that the deceleration rate matches the configured
RATE_LIMIT and VFD decel time (P0.12).

A smooth, controlled deceleration indicates proper rate
limiting and prevents mechanical stress.""",

            prerequisites=[
                "Basic tests completed",
                "VFD P0.12 (decel time) configured",
                "RATE_LIMIT matches VFD settings",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle accelerates to 1200 RPM",
                "3. Stop command (M5) issued",
                "4. Deceleration profile sampled",
                "5. Decel rate calculated and compared",
            ],

            expected_results=[
                "Smooth deceleration curve",
                "Decel rate ~matches RATE_LIMIT",
                "No abrupt stops or jerks",
                "Stop time ~consistent with VFD P0.12",
            ],

            troubleshooting=[
                "Decel much faster than accel:",
                "  -> Check VFD P0.12 matches P0.11",
                "Decel too slow:",
                "  -> Increase VFD P0.12 if needed",
                "Abrupt stop:",
                "  -> May indicate limit2 issue",
            ],

            safety_notes=[
                "Test starts at 1200 RPM",
                "Spindle stops during test",
            ]
        )

    def run(self):
        """Start deceleration test in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute deceleration test."""
        self.log_header("DECELERATION TEST: 1200 -> 0 RPM")
        self.update_progress(0, "Accelerating to 1200 RPM...")

        self.hal.send_mdi("M3 S1200")
        self.log_result("Accelerating to 1200 RPM...")
        time.sleep(3.5)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        self.log_result("Stopping (M5)...")
        self.update_progress(30, "Sampling deceleration...")

        test_data = []
        start = time.time()
        self.hal.send_mdi("M5")

        while time.time() - start < 4.0:
            if self.test_abort:
                break

            t = time.time() - start
            fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
            test_data.append((t, fb))

            progress = 30 + (t / 4.0) * 50
            self.update_progress(progress, f"Decelerating... {fb:.0f} RPM")

            time.sleep(0.05)

        self.update_progress(85, "Calculating rate...")

        if not test_data:
            self.end_test()
            return

        # Find time to reach <100 RPM
        stop_time = None
        for t, fb in test_data:
            if fb < 100:
                stop_time = t
                break

        # Calculate average decel rate
        if len(test_data) > 2:
            decel_rate = (test_data[0][1] - test_data[-1][1]) / \
                         (test_data[-1][0] - test_data[0][0])
        else:
            decel_rate = 0

        self.log_result(f"\nResults:")
        if stop_time:
            self.log_result(f"  Time to <100 RPM: {stop_time:.2f} s")
        else:
            self.log_result(f"  Did not stop within window")
        self.log_result(f"  Average decel rate: {decel_rate:.0f} RPM/s")

        rate_limit = self.hal.get_param('RateLimit')
        self.update_progress(100, "Complete")

        if rate_limit > 0 and decel_rate > 0:
            if abs(decel_rate - rate_limit) / rate_limit < 0.3:
                self.log_footer("PASS")
                self.log_result(f"  Decel matches RATE_LIMIT ({rate_limit:.0f})")
            else:
                self.log_footer("COMPLETE")
                self.log_result(f"  Decel differs from RATE_LIMIT ({rate_limit:.0f})")
        else:
            self.log_footer("COMPLETE")

        self.end_test()
