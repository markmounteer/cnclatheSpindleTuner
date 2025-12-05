"""
Rate Limit Test (Guide §6.4)

Verifies limit2 component enforces command rate limiting.
"""

import time
from typing import Optional

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

        # Ensure spindle is stopped before starting the ramp
        self.hal.send_mdi("M5")
        time.sleep(1.0)

        target_rpm = 1500
        rate_limit_cfg: Optional[float] = self.hal.get_param("RateLimit")

        if rate_limit_cfg is None:
            self.log_result("RATE_LIMIT parameter not found in HAL")
            self.log_footer("CANNOT EVALUATE")
            self.end_test()
            return

        self.log_result(f"\nConfigured RATE_LIMIT: {rate_limit_cfg:.0f} RPM/s")
        self.log_result(f"Commanding M3 S{target_rpm}...")
        self.update_progress(10, "Starting ramp...")

        start_time = time.perf_counter()
        times = []
        limited_vals = []
        raw_vals = []

        has_raw_pin = "cmd_raw" in MONITOR_PINS

        self.hal.send_mdi(f"M3 S{target_rpm}")

        sample_duration = 3.0
        sample_interval = 0.02
        while time.perf_counter() - start_time < sample_duration:
            if self.test_abort:
                break

            t = time.perf_counter() - start_time
            limited = self.hal.get_pin_value(MONITOR_PINS["cmd_limited"])

            times.append(t)
            limited_vals.append(limited)

            if has_raw_pin:
                raw_vals.append(self.hal.get_pin_value(MONITOR_PINS["cmd_raw"]))

            progress = 10 + (t / sample_duration) * 60
            self.update_progress(progress, f"Sampling ramp... {limited:.0f} RPM")

            time.sleep(sample_interval)

        self.hal.send_mdi("M5")
        self.update_progress(80, "Calculating rate...")

        if len(times) < 10 or self.test_abort:
            self.log_result(" Not enough samples or aborted")
            self.end_test()
            return

        threshold_10 = target_rpm * 0.1
        threshold_90 = target_rpm * 0.9

        if has_raw_pin and raw_vals:
            raw_step_time = next(
                (t for t, v in zip(times, raw_vals) if v >= target_rpm * 0.95),
                None,
            )
            if raw_step_time is not None and raw_step_time < 0.1:
                self.log_result("Raw command stepped immediately as expected")
            else:
                self.log_result("Warning: Raw command did not step immediately")

        indices = [
            i for i, v in enumerate(limited_vals) if threshold_10 <= v <= threshold_90
        ]
        if len(indices) < 3:
            indices = range(len(limited_vals))
            self.log_result(
                "Warning: Using full data for rate calculation (limited ramp detection)"
            )

        times_ramp = [times[i] for i in indices]
        limited_ramp = [limited_vals[i] for i in indices]

        if len(times_ramp) >= 2:
            x_mean = sum(times_ramp) / len(times_ramp)
            y_mean = sum(limited_ramp) / len(limited_ramp)

            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(times_ramp, limited_ramp))
            denominator = sum((x - x_mean) ** 2 for x in times_ramp)

            if denominator != 0:
                slope = numerator / denominator
                observed_rate = abs(slope)
            else:
                observed_rate = 0
                self.log_result("Error: Zero variance in time data")
        else:
            observed_rate = 0
            self.log_result("Error: Insufficient data for rate calculation")

        self.log_result("\nResults:")
        self.log_result(f" Limited final: {limited_vals[-1]:.0f} RPM")
        self.log_result(f" Observed ramp rate: {observed_rate:.0f} RPM/s")
        self.log_result(f" Configured rate: {rate_limit_cfg:.0f} RPM/s")

        self.update_progress(100, "Complete")

        if rate_limit_cfg <= 0:
            self.log_footer("CANNOT EVALUATE")
            self.log_result(" RATE_LIMIT not configured or invalid")
        else:
            rate_error = abs(observed_rate - rate_limit_cfg) / rate_limit_cfg

            if rate_error < 0.25:
                self.log_footer("PASS")
                self.log_result(" Ramp rate within 25% of configured")
                self.log_result(" limit2 component is working correctly")
            elif rate_error < 0.50:
                self.log_footer("MARGINAL")
                self.log_result(" Ramp rate within 50% of configured")
                self.log_result(" Check limit2 wiring in custom.hal")
            else:
                self.log_footer("FAIL")
                self.log_result(" Ramp rate differs significantly")
                self.log_result(" Verify limit2.0.maxv is set from RATE_LIMIT")

        self.end_test()
