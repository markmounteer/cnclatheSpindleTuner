"""Deceleration Test

Measures spindle deceleration behavior and rate.
"""

import time
from typing import List, Tuple

from config import MONITOR_PINS
from tests.base import BaseTest, ProcedureDescription


class DecelTest(BaseTest):
    """Deceleration test."""

    TEST_NAME = "Deceleration Test"
    GUIDE_REF = ""

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
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

        # Accelerate to target RPM
        target_rpm = 1200
        self.hal.send_mdi(f"M3 S{target_rpm}")
        self.log_result(f"Accelerating to {target_rpm} RPM...")

        # Wait for spindle to reach speed (adjustable timeout)
        accel_timeout = 5.0
        start_time = time.time()
        while time.time() - start_time < accel_timeout:
            if self.test_abort:
                self._cleanup()
                return
            current_rpm = self.hal.get_pin_value(MONITOR_PINS['feedback'])
            if current_rpm >= target_rpm * 0.95:  # Allow 5% tolerance
                break
            time.sleep(0.1)
        else:
            self.log_result("Timeout waiting for spindle to reach speed.")
            self.log_footer("FAIL")
            self._cleanup()
            return

        if self.test_abort:
            self._cleanup()
            return

        # Issue stop command
        self.log_result("Stopping (M5)...")
        self.update_progress(30, "Sampling deceleration...")
        test_data: List[Tuple[float, float]] = []
        start = time.time()
        self.hal.send_mdi("M5")

        # Sample deceleration (max 4 seconds or until near stop)
        sample_interval = 0.05
        max_duration = 4.0
        min_rpm_threshold = 100
        while time.time() - start < max_duration:
            if self.test_abort:
                break
            t = time.time() - start
            fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
            test_data.append((t, fb))
            progress = 30 + (t / max_duration) * 50
            self.update_progress(progress, f"Decelerating... {fb:.0f} RPM")
            if fb < min_rpm_threshold:
                break
            time.sleep(sample_interval)

        self.update_progress(85, "Calculating rate...")

        if not test_data:
            self.log_result("No data collected.")
            self.log_footer("FAIL")
            self._cleanup()
            return

        # Calculate time to reach <100 RPM
        stop_time = next((t for t, fb in test_data if fb < min_rpm_threshold), None)

        # Calculate average decel rate (only if data points available)
        decel_rate = 0.0
        if len(test_data) > 1:
            initial_rpm = test_data[0][1]
            final_rpm = test_data[-1][1]
            duration = test_data[-1][0] - test_data[0][0]
            if duration > 0:
                decel_rate = (initial_rpm - final_rpm) / duration

        # Log results
        self.log_result("\nResults:")
        if stop_time is not None:
            self.log_result(f" Time to <{min_rpm_threshold} RPM: {stop_time:.2f} s")
        else:
            self.log_result(f" Did not reach <{min_rpm_threshold} RPM within {max_duration:.1f} s")
        self.log_result(f" Average decel rate: {decel_rate:.0f} RPM/s")

        # Compare to RATE_LIMIT
        rate_limit = self.hal.get_param('RateLimit')  # Assuming case-sensitive
        if rate_limit > 0 and decel_rate > 0:
            tolerance = 0.3  # 30% tolerance
            if abs(decel_rate - rate_limit) / rate_limit < tolerance:
                self.log_result(f" Decel matches RATE_LIMIT ({rate_limit:.0f}) within {tolerance*100}%")
                self.log_footer("PASS")
            else:
                self.log_result(f" Decel differs from RATE_LIMIT ({rate_limit:.0f})")
                self.log_footer("COMPLETE")
        else:
            self.log_footer("COMPLETE")

        self.update_progress(100, "Complete")
        self._cleanup()

    def _cleanup(self):
        """Ensure spindle is stopped and end the test."""
        self.hal.send_mdi("M5")
        self.end_test()
