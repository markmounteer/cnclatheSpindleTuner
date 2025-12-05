"""
Pre-Flight Check Test (Guide §5, §14.3)

Comprehensive verification before tuning session.
"""

import time
import threading

from config import MONITOR_PINS, BASELINE_PARAMS
from tests.base import BaseTest, TestDescription


class PreflightTest(BaseTest):
    """Pre-flight verification test (Guide §5, §14.3)."""

    TEST_NAME = "Pre-Flight Check"
    GUIDE_REF = "Guide §5, §14.3"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Pre-Flight Check",
            guide_ref="§5, §14.3",
            purpose="""
Comprehensive pre-flight verification combining parameter validation,
DPLL configuration check, safety signal verification, and a brief
spin test to confirm basic spindle operation.

Run this test at the start of each tuning session to ensure the
system is properly configured and safe to operate.""",

            prerequisites=[
                "LinuxCNC loaded and machine power ON",
                "E-stop released and machine ready",
                "Spindle area clear of obstructions",
                "No workpiece or tooling installed",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. PID parameters compared to v5.3 baseline",
                "3. DPLL configuration verified (§5.4)",
                "4. Safety signals (external-ok) checked",
                "5. Brief spin test at 200 RPM confirms operation",
                "6. Results summarize all checks",
            ],

            expected_results=[
                "PID parameters within 25% of baseline",
                "DPLL timer configured (~100 or -100 us)",
                "external-ok signal TRUE (1.0)",
                "Spindle reaches ~200 RPM in brief test",
                "At-speed indicator activates",
            ],

            troubleshooting=[
                "Parameters FAR OFF: Check INI [SPINDLE_0] section",
                "DPLL disabled: Add dpll.01.timer-us config to HAL",
                "external-ok FALSE: Check E-stop and safety chain",
                "Low feedback: Check encoder wiring and scale",
                "No at-speed: Adjust AT_SPEED_TOLERANCE in INI",
            ],

            safety_notes=[
                "Brief spin test runs at low speed (200 RPM)",
                "Keep hand near E-stop during test",
                "Spindle stops automatically after test",
            ]
        )

    def run(self):
        """Start pre-flight check in background thread."""
        if not self.start_test():
            return
        threading.Thread(target=self._sequence, daemon=True).start()

    def _sequence(self):
        """Execute pre-flight checks."""
        self.log_header()
        self.update_progress(0, "Starting pre-flight checks...")

        all_ok = True

        # 1. Check PID parameters vs baseline
        self.log_result("\n1. PID Parameters vs Baseline:")
        self.update_progress(10, "Checking PID parameters...")

        for param in ['P', 'I', 'FF0', 'FF1', 'Deadband', 'MaxErrorI', 'RateLimit']:
            current = self.hal.get_param(param)
            expected = BASELINE_PARAMS.get(param, 0)
            diff_pct = abs(current - expected) / max(expected, 0.001) * 100

            if diff_pct < 25:
                status = "[OK]"
            elif diff_pct < 50:
                status = "[DIFFERS]"
                all_ok = False
            else:
                status = "[FAR OFF]"
                all_ok = False

            self.log_result(f"   {param}: {current:.3f} (baseline {expected}) - {status}")

        # 2. DPLL verification (Guide §5.4)
        self.log_result("\n2. DPLL Configuration (§5.4):")
        self.update_progress(30, "Checking DPLL...")

        dpll_timer = self.hal.get_pin_value('hm2_7i76e.0.dpll.01.timer-us')
        if abs(dpll_timer - (-100)) < 20 or abs(dpll_timer - 100) < 20:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}us - [OK]")
        elif dpll_timer == 0:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}us - [MAY BE DISABLED]")
            all_ok = False
        else:
            self.log_result(f"   DPLL timer: {dpll_timer:.0f}us - [Non-zero]")

        # 3. Safety signals
        self.log_result("\n3. Safety Signals:")
        self.update_progress(50, "Checking safety signals...")

        ext_ok = self.hal.get_pin_value(MONITOR_PINS.get('external_ok', 'external-ok'))

        if ext_ok > 0.5:
            self.log_result(f"   external-ok: {ext_ok:.0f} - [OK]")
        else:
            self.log_result(f"   external-ok: {ext_ok:.0f} - [NOT OK]")
            all_ok = False

        # 4. Brief spin test
        self.log_result("\n4. Brief Spin Test:")
        self.update_progress(60, "Running brief spin test...")

        self.log_result("   Starting M3 S200...")
        self.hal.send_mdi("M3 S200")
        time.sleep(3.0)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.log_result("   ABORTED")
            self.end_test()
            return

        fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        fb_abs = self.hal.get_pin_value(MONITOR_PINS['feedback_abs'])
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])

        self.hal.send_mdi("M5")
        self.update_progress(90, "Analyzing results...")

        if fb > 100:
            self.log_result(f"   Feedback: {fb:.0f} RPM - [OK]")
        else:
            self.log_result(f"   Feedback: {fb:.0f} RPM - [LOW/WRONG]")
            all_ok = False

        if fb_abs > 100:
            self.log_result(f"   ABS feedback: {fb_abs:.0f} RPM - [OK]")
        else:
            self.log_result(f"   ABS feedback: {fb_abs:.0f} RPM - [CHECK]")
            all_ok = False

        if at_speed > 0.5:
            self.log_result(f"   At-speed: YES - [OK]")
        else:
            self.log_result(f"   At-speed: NO - [Did not reach speed]")

        self.update_progress(100, "Complete")

        if all_ok:
            self.log_footer("PASS - ALL CHECKS PASSED")
            self.log_result("Ready for tuning session.")
        else:
            self.log_footer("WARNING - ISSUES FOUND")
            self.log_result("Review warnings before proceeding.")

        self.end_test()
