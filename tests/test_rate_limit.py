"""
Rate Limit Test (Guide §6.4)

Verifies limit2 component enforces command rate limiting.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription


class RateLimitTest(BaseTest):
    """Rate limit verification test (Guide §6.4)."""

    TEST_NAME = "Rate Limit Test"
    GUIDE_REF = "Guide §6.4"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Rate Limit Verification",
            guide_ref="§6.4",
            purpose="""
Verify that the limit2 component properly rate-limits command
changes to match VFD acceleration capability (1200 RPM/s default).

Without rate limiting, step commands cause integrator windup
during the VFD's ramp time, resulting in overshoot.""",

            prerequisites=[
                "LinuxCNC loaded and limit2 component configured",
                "custom.hal should have limit2 in command path",
                "RATE_LIMIT parameter set in INI file",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle stopped initially",
                "3. Command stepped to 1500 RPM",
                "4. Rate-limited signal sampled during ramp",
                "5. Observed ramp rate compared to configured limit",
            ],

            expected_results=[
                "Raw command steps immediately to 1500",
                "Limited command ramps at ~1200 RPM/s",
                "Ramp time: ~1.25 seconds (1500/1200)",
                "Observed rate within 25% of configured",
            ],

            troubleshooting=[
                "Both signals step instantly:",
                "  -> limit2 not connected in custom.hal",
                "  -> Check signal routing in HAL files",
                "Rate much faster than configured:",
                "  -> limit2.maxv not set from RATE_LIMIT",
                "Rate much slower:",
                "  -> VFD acceleration time too long",
            ],

            safety_notes=[
                "Test runs up to 1500 RPM",
                "Tests command path, not actual speed",
            ]
        )

    def run(self):
        """Start rate limit test in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute rate limit test."""
        self.log_header()
        self.log_result("Verifies limit2 component enforces RATE_LIMIT")
        self.update_progress(0, "Preparing test...")

        self.hal.send_mdi("M5")
        time.sleep(1.0)

        target = 1500
        rate_limit_cfg = self.hal.get_param('RateLimit')

        self.log_result(f"\nConfigured RATE_LIMIT: {rate_limit_cfg:.0f} RPM/s")
        self.log_result(f"Commanding M3 S{target}...")
        self.update_progress(10, "Starting ramp...")

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

            progress = 10 + (t / duration) * 60
            self.update_progress(progress, f"Sampling ramp... {limited:.0f} RPM")

            time.sleep(0.05)

        self.hal.send_mdi("M5")
        self.update_progress(80, "Calculating rate...")

        if len(times) < 5 or self.test_abort:
            self.log_result("  Not enough samples or aborted")
            self.end_test()
            return

        # Calculate observed ramp rate (10% to 90%)
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

        self.update_progress(100, "Complete")

        if rate_limit_cfg > 0:
            rate_error = abs(observed_rate - rate_limit_cfg) / rate_limit_cfg

            if rate_error < 0.25:
                self.log_footer("PASS")
                self.log_result("  Ramp rate within 25% of configured")
                self.log_result("  limit2 component is working correctly")
            elif rate_error < 0.50:
                self.log_footer("MARGINAL")
                self.log_result("  Ramp rate within 50% of configured")
                self.log_result("  Check limit2 wiring in custom.hal")
            else:
                self.log_footer("FAIL")
                self.log_result("  Ramp rate differs significantly")
                self.log_result("  Verify limit2.0.maxv is set from RATE_LIMIT")
        else:
            self.log_footer("CANNOT EVALUATE")
            self.log_result("  RATE_LIMIT not configured")

        self.end_test()
