"""
Steady-State Test (Guide §7.3)

Monitors steady-state accuracy and thermal drift over time.
"""

import time
import threading

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription, TARGETS


class SteadyStateTest(BaseTest):
    """Steady-state accuracy test (Guide §7.3)."""

    TEST_NAME = "Steady-State Test"
    GUIDE_REF = "Guide §7.3"

    def __init__(self, *args, duration: int = 30, **kwargs):
        super().__init__(*args, **kwargs)
        self.duration = duration

    def set_duration(self, duration: int):
        """Set the monitoring duration in seconds."""
        self.duration = max(10, min(300, duration))

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Steady-State Accuracy Test",
            guide_ref="§7.3",
            purpose="""
Monitor spindle speed stability over an extended period.
Measures:

- Average error from setpoint
- Speed variation (min/max/std deviation)
- Integrator drift (indicates thermal compensation)

Longer durations (60-120s) reveal thermal drift as the
motor heats up and slip increases.""",

            prerequisites=[
                "Step and load tests completed",
                "Spindle warmed up for accurate results",
                "For thermal drift, run 2-5 minutes",
            ],

            procedure=[
                "1. Set desired duration in the UI (default 30s)",
                "2. Click 'Run Test' to begin",
                "3. Spindle runs at 1000 RPM",
                "4. Error and feedback sampled continuously",
                "5. Statistics calculated at end",
                "6. Integrator drift shows thermal compensation",
            ],

            expected_results=[
                "Steady-state error: <8 RPM EXCELLENT, <15 RPM GOOD",
                "Peak-to-peak variation: <10 RPM EXCELLENT, <20 RPM GOOD",
                "Integrator drift: Normal to see 5-20 increase over minutes",
                "No oscillation or hunting",
            ],

            troubleshooting=[
                "High variation (>20 RPM pk-pk):",
                "  -> Reduce P-gain",
                "  -> Increase deadband",
                "Large steady-state error:",
                "  -> Increase I-gain",
                "  -> Check maxerrorI not limiting",
                "Integrator not drifting (should increase):",
                "  -> I-gain may be too low",
                "  -> maxerrorI may be limiting",
            ],

            safety_notes=[
                "Test runs at 1000 RPM",
                "Duration configurable (10-300 seconds)",
                "Longer tests reveal thermal behavior",
            ]
        )

    def run(self, duration: int = None):
        """Start steady-state test with optional duration."""
        if duration is not None:
            self.set_duration(duration)

        if not self.start_test():
            return

        threading.Thread(target=self._sequence, daemon=True).start()

    def _sequence(self):
        """Execute steady-state monitoring."""
        self.log_header(f"STEADY-STATE ACCURACY TEST ({self.duration}s)")
        self.update_progress(0, "Stabilizing at 1000 RPM...")

        self.hal.send_mdi("M3 S1000")
        self.log_result("Stabilizing at 1000 RPM...")
        time.sleep(4)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        self.log_result(f"Monitoring for {self.duration} seconds...")
        self.update_progress(5, "Monitoring...")

        errors = []
        rpms = []
        integrators = []
        start = time.time()

        while time.time() - start < self.duration:
            if self.test_abort:
                break

            errors.append(self.hal.get_pin_value(MONITOR_PINS['error']))
            rpms.append(self.hal.get_pin_value(MONITOR_PINS['feedback']))
            integrators.append(self.hal.get_pin_value(MONITOR_PINS['errorI']))

            elapsed = time.time() - start
            progress = 5 + (elapsed / self.duration) * 85
            self.update_progress(progress, f"Monitoring... {elapsed:.0f}s")

            time.sleep(0.2)

        self.hal.send_mdi("M5")
        self.update_progress(95, "Calculating statistics...")

        if not rpms or self.test_abort:
            self.log_result("  Test aborted or no data")
            self.end_test()
            return

        # Calculate statistics
        stats = self.calculate_statistics(rpms)
        integrator_drift = integrators[-1] - integrators[0]
        ss_error = 1000.0 - stats['avg']

        self.log_result(f"\nRESULTS:")
        self.log_result(f"  Average RPM: {stats['avg']:.1f}")
        self.log_result(f"  Std deviation: {stats['std_dev']:.2f} RPM")
        self.log_result(f"  Min/Max: {stats['min']:.1f} / {stats['max']:.1f} RPM")
        self.log_result(f"  Peak-to-peak: {stats['range']:.1f} RPM")
        self.log_result(f"  Steady-state error: {ss_error:.1f} RPM")
        self.log_result(f"  Integrator drift: {integrator_drift:+.1f}")

        self.log_result(f"\nASSESSMENT (Guide §7.4):")
        self.log_result(f"  SS Error: {self.assess_ss_error(ss_error)}")
        self.log_result(f"  Stability: {self.assess_noise(stats['range'])}")

        if abs(integrator_drift) > 20:
            self.log_result(f"\n  Note: Integrator drifted {integrator_drift:+.1f}")
            self.log_result("    (Normal - I-term compensating for motor heating)")

        self.update_progress(100, "Complete")

        if stats['range'] <= TARGETS.noise_excellent and abs(ss_error) <= TARGETS.ss_error_excellent:
            self.log_footer("EXCELLENT")
        elif stats['range'] <= TARGETS.noise_good and abs(ss_error) <= TARGETS.ss_error_good:
            self.log_footer("GOOD")
        else:
            self.log_footer("NEEDS TUNING")

        self.end_test()
