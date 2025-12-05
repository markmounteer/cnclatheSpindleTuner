"""
Signal Chain Integrity Test (Guide §5.1)

Validates HAL signal chain connectivity and baseline parameters prior to system
tuning. Ensures all critical signals are accessible and PID values are
correctly initialized.
"""

from config import MONITOR_PINS, BASELINE_PARAMS
from tests.base import BaseTest, TestDescription


class SignalChainTest(BaseTest):
    """Signal chain integrity validation test (Guide §5.1)."""

    TEST_NAME = "Signal Chain Integrity Check"
    GUIDE_REF = "Guide §5.1"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Signal Chain Integrity Check",
            guide_ref="§5.1",
            purpose="""
Verify the integrity of the HAL signal chain from command inputs through PID
computations to feedback signals. This test confirms proper connectivity and
baseline parameter loading without requiring spindle operation. It serves as
the initial pre-flight check to ensure the system is ready for further testing
and tuning.""",
            prerequisites=[
                "LinuxCNC instance loaded (machine power may remain OFF)",
                "HAL configuration files correctly loaded and active",
                "No spindle motion or active commands required",
            ],
            procedure=[
                "1. Initiate the test by clicking 'Run Test'",
                "2. System automatically queries all monitored HAL pins",
                "3. PID parameters are cross-verified against baseline expectations",
                "4. Connectivity and value validity are assessed for each signal",
                "5. Any discrepancies or failures are highlighted in the results",
            ],
            expected_results=[
                "All monitored HAL pins should be accessible and return valid values (even if zero)",
                "PID parameters (P, I, FF0, FF1) should align with baseline configurations",
                "At-speed indicator should report either 0 or 1",
                "Safety interlocks (e.g., external-ok) should indicate TRUE (1)",
            ],
            troubleshooting=[
                "Pin access errors: Verify HAL pin names and configuration integrity",
                "Zero or mismatched PID params: Inspect INI file [SPINDLE_0] section",
                "Missing signals: Review custom.hal for proper signal linkages",
                "In mock mode, expect simulated baseline values",
            ],
            safety_notes=[
                "Test is non-invasive and does not initiate spindle movement",
                "Safe to execute with machine power disconnected",
            ],
        )

    def run(self):
        """Initiate signal chain integrity check in a background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Perform the signal chain integrity checks."""
        self.log_header()

        pass_count = 0
        fail_count = 0

        def format_value(value: object) -> str:
            return f"{float(value):.2f}" if isinstance(value, (int, float)) else str(value)

        # Define HAL pin checks with validators for value sanity
        checks = [
            (MONITOR_PINS.get("cmd_raw", "spindle-vel-cmd-rpm-raw"),
             "Raw command signal", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("cmd_limited", "spindle-vel-cmd-rpm-limited"),
             "Rate-limited command", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("feedback", "spindle-vel-fb-rpm"),
             "Velocity feedback", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("feedback_abs", "spindle-vel-fb-rpm-abs"),
             "Absolute feedback", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("error", "pid.s.error"),
             "PID error signal", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("errorI", "pid.s.errorI"),
             "PID integrator", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("output", "pid.s.output"),
             "PID output", lambda v: isinstance(v, (int, float))),
            (MONITOR_PINS.get("at_speed", "spindle-is-at-speed"),
             "At-speed indicator", lambda v: v in [0.0, 1.0]),
            (MONITOR_PINS.get("external_ok", "external-ok"),
             "External safety OK", lambda v: v == 1.0),
        ]

        self.log_result("\nVerifying HAL signal chain connectivity:")

        for pin_name, desc, validator in checks:
            try:
                value = self.hal.get_pin_value(pin_name)
                if validator(value):
                    self.log_result(f" [PASS] {desc}: {format_value(value)}")
                    pass_count += 1
                else:
                    self.log_result(f" [FAIL] {desc}: {format_value(value)} (invalid value)")
                    fail_count += 1
            except Exception as e:
                self.log_result(f" [FAIL] {desc}: ERROR - {e} (pin may be missing or inaccessible)")
                fail_count += 1

        self.log_result("\nVerifying PID parameter initialization:")
        tolerance = 0.001
        for param in ["P", "I", "FF0", "FF1"]:
            try:
                value = self.hal.get_param(param)
                expected = BASELINE_PARAMS.get(param, 0.0)
                if abs(value - expected) <= tolerance:
                    self.log_result(f" [PASS] {param}: {value:.3f} (matches expected ~{expected:.3f})")
                    pass_count += 1
                else:
                    self.log_result(f" [FAIL] {param}: {value:.3f} (expected ~{expected:.3f})")
                    fail_count += 1
            except Exception as e:
                self.log_result(f" [FAIL] {param}: ERROR - {e} (parameter may not be loaded)")
                fail_count += 1

        total_checks = pass_count + fail_count
        if fail_count == 0:
            self.log_footer(f"PASS - All {total_checks} checks completed successfully")
        else:
            self.log_footer(f"FAIL - {fail_count}/{total_checks} issues detected; review logs for details")

        self.end_test()
