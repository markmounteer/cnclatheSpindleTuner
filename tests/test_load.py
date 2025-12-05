"""
Load Recovery Test (Guide §7.2)

Interactive test to measure load disturbance rejection.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription, TARGETS


class LoadTest(BaseTest):
    """Interactive load recovery test (Guide §7.2)."""

    TEST_NAME = "Load Recovery Test"
    GUIDE_REF = "Guide §7.2"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Interactive Load Test",
            guide_ref="§7.2",
            purpose="""
Measure the system's ability to reject load disturbances and
recover to the setpoint. This tests the I-term's effectiveness
at compensating for cutting loads.

The test is INTERACTIVE - you apply friction to the chuck
when prompted, then release to measure recovery.""",

            prerequisites=[
                "Step Response Test completed",
                "Spindle running at stable speed",
                "Safe method to apply light load (wooden stick)",
                "Do NOT use your hand directly on chuck",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle stabilizes at 1000 RPM",
                "3. When prompted, apply light friction",
                "   (Use wooden dowel against chuck surface)",
                "4. Hold for ~3 seconds to see droop",
                "5. Release to measure recovery time",
                "6. Recovery time and droop measured",
            ],

            expected_results=[
                "Recovery time: <2s EXCELLENT, <3s GOOD",
                "Max droop: Depends on load magnitude",
                "Speed returns to within +/-20 RPM of target",
                "No oscillation after recovery",
            ],

            troubleshooting=[
                "Slow recovery (>3s):",
                "  -> Increase I-gain from 1.0 to 1.2-1.5",
                "  -> Check maxerrorI not limiting",
                "Does not recover fully:",
                "  -> Increase maxerrorI limit",
                "  -> errorI may be saturating",
                "Oscillation after release:",
                "  -> Reduce I-gain slightly",
            ],

            safety_notes=[
                ">>> NEVER touch spinning chuck with bare hands <<<",
                "Use wooden stick or dowel for friction",
                "Keep clear of rotating parts",
                "Spindle continues running after test",
            ]
        )

    def run(self):
        """Start load recovery test in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute load recovery test."""
        self.log_header()
        self.update_progress(0, "Stabilizing at 1000 RPM...")

        try:
            self.hal.send_mdi("M3 S1000")
            self.log_result("Stabilizing at 1000 RPM...")
            time.sleep(4)  # Allow time for stabilization

            if self.test_abort:
                self._cleanup()
                return

            self.update_progress(20, "Measuring baseline...")
            _, baseline_samples = self.sample_signal(MONITOR_PINS['feedback'], 1.0, 0.1)
            baseline = sum(baseline_samples) / len(baseline_samples) if baseline_samples else 1000
            self.log_result(f"Baseline: {baseline:.0f} RPM")

            self.log_result("\n" + "="*50)
            self.log_result(">>> Apply load NOW (wooden stick against chuck) <<<")
            self.log_result(">>> Hold for 3 seconds, then release <<<")
            self.log_result("="*50)
            self.update_progress(30, ">>> APPLY LOAD NOW <<<")

            min_rpm = baseline
            max_droop = 0
            samples = []
            start = time.time()
            monitor_duration = 10.0  # Configurable monitor window

            while time.time() - start < monitor_duration:
                if self.test_abort:
                    self._cleanup()
                    return

                fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
                t = time.time() - start
                samples.append((t, fb))

                if fb < min_rpm:
                    min_rpm = fb
                    max_droop = baseline - min_rpm

                progress = 30 + (t / monitor_duration) * 50
                self.update_progress(progress, f"Monitoring... {fb:.0f} RPM")
                time.sleep(0.1)

            self.update_progress(85, "Calculating recovery...")

            # Calculate recovery metrics using shared logger logic
            metrics = self.logger.calculate_load_metrics(samples, baseline)
            recovery_time = metrics.load_recovery_time_s if metrics.load_recovery_time_s > 0 else None

            self.log_result(f"\nResults:")
            self.log_result(f" Baseline: {baseline:.0f} RPM")
            self.log_result(f" Minimum during load: {min_rpm:.0f} RPM")
            self.log_result(f" Max droop: {max_droop:.0f} RPM ({max_droop / baseline * 100:.1f}%)")

            self.update_progress(100, "Complete")

            if recovery_time:
                self.log_result(f" Recovery time: {recovery_time:.2f} s")
                assessment = self.assess_recovery(recovery_time)
                self.log_result(f"\nASSESSMENT: {assessment}")
                if recovery_time > TARGETS.recovery_good:
                    self.log_result(" -> Consider increasing I-gain or MaxErrorI")
                    self.log_footer("SLOW RECOVERY")
                elif recovery_time > TARGETS.recovery_excellent:
                    self.log_footer("GOOD")
                else:
                    self.log_footer("EXCELLENT")
            else:
                self.log_result(" Recovery time: Did not recover within window")
                self.log_result(" -> May need more I-gain for load rejection")
                self.log_footer("NO RECOVERY DETECTED")

            self.log_result("\n>>> Spindle still running - stop manually when ready <<<")

        except Exception as e:
            self.log_result(f"Error during test: {str(e)}")
            self.log_footer("TEST FAILED")
        finally:
            self.end_test()

    def _cleanup(self):
        """Cleanup spindle on abort or error."""
        self.hal.send_mdi("M5")
        self.end_test()

    def assess_recovery(self, recovery_time: float) -> str:
        """Assess recovery time based on targets."""
        if recovery_time < TARGETS.recovery_excellent:
            return "EXCELLENT"
        elif recovery_time < TARGETS.recovery_good:
            return "GOOD"
        else:
            return "SLOW"
