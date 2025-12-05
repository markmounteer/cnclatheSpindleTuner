"""
Pre-Flight Check Test (Guide §5, §14.3)

Comprehensive verification before tuning session.
"""

import time

from config import MONITOR_PINS, BASELINE_PARAMS
from tests.base import BaseTest, TestDescription


# =============================================================================
# PREFLIGHT TEST CONSTANTS
# =============================================================================

# PID parameter tolerance thresholds (percentage)
PID_TOLERANCE_WARN = 25   # % difference for OK status
PID_TOLERANCE_FAIL = 50   # % difference for DIFFERS vs FAR OFF

# DPLL configuration expectations
DPLL_EXPECTED_US = 100    # Expected absolute value (±100 us)
DPLL_TOLERANCE_US = 20    # Acceptable deviation from expected

# Spin test thresholds
SPIN_TEST_RPM = 200       # Target RPM for brief spin test
SPIN_MIN_RPM = 100        # Minimum acceptable feedback RPM
SPIN_STABILIZE_S = 3.0    # Time to allow spindle to ramp up
SPIN_STOP_WAIT_S = 1.0    # Time to wait after stop command

# PID parameters to check against baseline
PID_PARAMS = ['P', 'I', 'FF0', 'FF1', 'Deadband', 'MaxErrorI', 'RateLimit']


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
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute pre-flight checks."""
        self.log_header()
        self.update_progress(0, "Starting pre-flight checks...")
        all_ok = True

        try:
            # 1. Check PID parameters vs baseline
            self.log_result("\n1. PID Parameters vs Baseline:")
            self.update_progress(10, "Checking PID parameters...")

            for param in PID_PARAMS:
                try:
                    current = self.hal.get_param(param)
                    expected = BASELINE_PARAMS.get(param, 0)
                    diff_pct = abs(current - expected) / max(abs(expected), 0.001) * 100

                    if diff_pct < PID_TOLERANCE_WARN:
                        status = "[OK]"
                    elif diff_pct < PID_TOLERANCE_FAIL:
                        status = "[DIFFERS]"
                        all_ok = False
                    else:
                        status = "[FAR OFF]"
                        all_ok = False

                    self.log_result(f"   {param}: {current:.3f} (baseline {expected}) - {status}")
                except Exception as e:
                    self.log_result(f"   {param}: Error reading value - [FAIL] ({e})")
                    all_ok = False

            # 2. DPLL verification (Guide §5.4)
            self.log_result("\n2. DPLL Configuration (§5.4):")
            self.update_progress(30, "Checking DPLL...")

            try:
                dpll_pin = MONITOR_PINS.get('dpll_timer', 'hm2_7i76e.0.dpll.01.timer-us')
                dpll_timer = self.hal.get_pin_value(dpll_pin)

                if abs(abs(dpll_timer) - DPLL_EXPECTED_US) < DPLL_TOLERANCE_US:
                    self.log_result(f"   DPLL timer ({dpll_pin}): {dpll_timer:.0f}us - [OK]")
                elif dpll_timer == 0:
                    self.log_result(f"   DPLL timer ({dpll_pin}): {dpll_timer:.0f}us - [MAY BE DISABLED]")
                    all_ok = False
                else:
                    self.log_result(f"   DPLL timer ({dpll_pin}): {dpll_timer:.0f}us - [UNEXPECTED VALUE]")
                    all_ok = False
            except Exception as e:
                self.log_result(f"   DPLL timer: Error reading value - [FAIL] ({e})")
                all_ok = False

            # 3. Safety signals
            self.log_result("\n3. Safety Signals:")
            self.update_progress(50, "Checking safety signals...")

            try:
                ext_ok_pin = MONITOR_PINS.get('external_ok', 'external-ok')
                ext_ok = self.hal.get_pin_value(ext_ok_pin)

                if ext_ok > 0.5:
                    self.log_result(f"   {ext_ok_pin}: {ext_ok:.0f} - [OK]")
                else:
                    self.log_result(f"   {ext_ok_pin}: {ext_ok:.0f} - [NOT OK]")
                    all_ok = False
            except Exception as e:
                self.log_result(f"   Safety signal: Error reading value - [FAIL] ({e})")
                all_ok = False

            # 4. Brief spin test
            self.log_result("\n4. Brief Spin Test:")
            self.update_progress(60, "Running brief spin test...")

            try:
                self.log_result(f"   Starting M3 S{SPIN_TEST_RPM}...")
                self.hal.send_mdi(f"M3 S{SPIN_TEST_RPM}")
                time.sleep(SPIN_STABILIZE_S)

                if self.check_abort():
                    self.log_result("   Spin test aborted by user.")
                    return

                fb_pin = MONITOR_PINS.get('feedback', 'pid.s.feedback')
                fb_abs_pin = MONITOR_PINS.get('feedback_abs', 'spindle-vel-fb-rpm-abs')
                at_speed_pin = MONITOR_PINS.get('at_speed', 'spindle-is-at-speed')

                fb = self.hal.get_pin_value(fb_pin)
                fb_abs = self.hal.get_pin_value(fb_abs_pin)
                at_speed = self.hal.get_pin_value(at_speed_pin)

                self.update_progress(90, "Analyzing results...")

                if fb > SPIN_MIN_RPM:
                    self.log_result(f"   Feedback ({fb_pin}): {fb:.0f} RPM - [OK]")
                else:
                    self.log_result(f"   Feedback ({fb_pin}): {fb:.0f} RPM - [LOW/WRONG]")
                    all_ok = False

                if fb_abs > SPIN_MIN_RPM:
                    self.log_result(f"   ABS feedback ({fb_abs_pin}): {fb_abs:.0f} RPM - [OK]")
                else:
                    self.log_result(f"   ABS feedback ({fb_abs_pin}): {fb_abs:.0f} RPM - [CHECK]")
                    all_ok = False

                if at_speed > 0.5:
                    self.log_result(f"   At-speed ({at_speed_pin}): YES - [OK]")
                else:
                    self.log_result(f"   At-speed ({at_speed_pin}): NO - [Did not reach speed]")
                    all_ok = False
            except Exception as e:
                self.log_result(f"   Spin test error - [FAIL] ({e})")
                all_ok = False
            finally:
                # Always stop the spindle after the spin test
                self.log_result("   Stopping spindle (M5)...")
                self.hal.send_mdi("M5")
                time.sleep(SPIN_STOP_WAIT_S)

            self.update_progress(100, "Complete")

            if all_ok:
                self.log_footer("PASS - ALL CHECKS PASSED")
                self.log_result("Ready for tuning session.")
            else:
                self.log_footer("WARNING - ISSUES FOUND")
                self.log_result("Review warnings before proceeding.")

        except Exception as e:
            self.log_result(f"\nUnexpected error during pre-flight checks: {e}")
            self.log_footer("FAIL - TEST ERROR")
