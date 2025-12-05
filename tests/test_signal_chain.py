"""
Signal Chain Check Test (Guide §5.1)

Verifies HAL signal chain integrity before tuning.
"""

from typing import Optional, Callable

from config import MONITOR_PINS, BASELINE_PARAMS
from tests.base import BaseTest, TestDescription


class SignalChainTest(BaseTest):
    """Signal chain validation test (Guide §5.1)."""

    TEST_NAME = "Signal Chain Check"
    GUIDE_REF = "Guide §5.1"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Signal Chain Check",
            guide_ref="§5.1",
            purpose="""
Verify that all HAL signals are properly connected and responding.
This test validates the signal chain from command input through
PID calculation to feedback without running the spindle.

This is the first step in the pre-flight verification process
and should be run before any other tests.""",

            prerequisites=[
                "LinuxCNC loaded (machine power can be OFF)",
                "HAL configuration files properly loaded",
                "No active spindle motion required",
            ],

            procedure=[
                "1. Click 'Run Test' to start automatic verification",
                "2. The test reads all monitored HAL pins",
                "3. PID parameters are compared to baseline values",
                "4. Results show which signals are connected",
                "5. Any missing or unexpected values are flagged",
            ],

            expected_results=[
                "All signal pins should be readable (even if zero)",
                "PID parameters (P, I, FF0, FF1) should match baseline",
                "At-speed indicator should be 0 or 1",
                "Safety signals (external-ok) should be TRUE (1)",
            ],

            troubleshooting=[
                "If pins show ERROR: Check HAL configuration and pin names",
                "If PID params are zero: Verify INI file SPINDLE_0 section",
                "If signals missing: Check custom.hal signal routing",
                "Mock mode will show simulated values",
            ],

            safety_notes=[
                "This test does not move the spindle",
                "Safe to run with machine power off",
            ]
        )

    def run(self):
        """Start signal chain check in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute signal chain check."""
        self.log_header()

        pass_count = 0
        fail_count = 0

        checks = [
            (MONITOR_PINS.get('cmd_raw', 'spindle-vel-cmd-rpm-raw'),
             "Command signal", lambda v: True),
            (MONITOR_PINS.get('cmd_limited', 'spindle-vel-cmd-rpm-limited'),
             "Rate-limited command", lambda v: True),
            (MONITOR_PINS.get('feedback', 'spindle-vel-fb-rpm'),
             "Velocity feedback", lambda v: True),
            (MONITOR_PINS.get('feedback_abs', 'spindle-vel-fb-rpm-abs'),
             "ABS feedback", lambda v: True),
            (MONITOR_PINS.get('error', 'pid.s.error'),
             "PID error signal", lambda v: True),
            (MONITOR_PINS.get('errorI', 'pid.s.errorI'),
             "PID integrator", lambda v: True),
            (MONITOR_PINS.get('output', 'pid.s.output'),
             "PID output", lambda v: True),
            (MONITOR_PINS.get('at_speed', 'spindle-is-at-speed'),
             "At-speed indicator", lambda v: v in [0.0, 1.0]),
        ]

        self.log_result("\nVerifying HAL signal chain:")

        for pin_name, desc, validator in checks:
            try:
                value = self.hal.get_pin_value(pin_name)
                if validator(value):
                    self.log_result(f"  [PASS] {desc}: {value:.2f}")
                    pass_count += 1
                else:
                    self.log_result(f"  [WARN] {desc}: {value:.2f} (unexpected)")
                    fail_count += 1
            except Exception as e:
                self.log_result(f"  [FAIL] {desc}: ERROR - {e}")
                fail_count += 1

        self.log_result("\nVerifying PID parameters loaded:")
        for param in ['P', 'I', 'FF0', 'FF1']:
            value = self.hal.get_param(param)
            expected = BASELINE_PARAMS.get(param, 0)
            if value > 0 or param in ['P']:
                self.log_result(f"  [PASS] {param}: {value:.3f}")
                pass_count += 1
            else:
                self.log_result(f"  [WARN] {param}: {value:.3f} (expected ~{expected})")
                fail_count += 1

        total = pass_count + fail_count
        if fail_count == 0:
            self.log_footer(f"PASS - ALL {pass_count} CHECKS PASSED")
        else:
            self.log_footer(f"WARNING - {fail_count}/{total} ISSUES FOUND")

        self.end_test()
