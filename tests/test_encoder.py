"""
Encoder Verification Test (Guide §5.2, §12.2)

Multi-speed encoder accuracy and polarity verification.
"""

import time
from typing import Dict, List, Tuple

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription, TARGETS


class EncoderTest(BaseTest):
    """Encoder verification test (Guide §5.2, §12.2)."""

    TEST_NAME = "Encoder Verification"
    GUIDE_REF = "Guide §5.2, §12.2"

    # Test speeds: (RPM, description)
    SPEEDS: List[Tuple[int, str]] = [
        (100, "Low speed - DPLL sensitive"),
        (500, "Mid speed"),
        (1500, "High speed"),
    ]

    # Timing constants
    RAMP_UP_TIMEOUT: float = 10.0  # Max seconds to wait for spindle to stabilize
    RAMP_UP_CHECK_INTERVAL: float = 0.5  # Seconds between stability checks
    SAMPLE_DURATION: float = 2.0  # Duration to sample once stable
    SAMPLE_INTERVAL: float = 0.1  # Sampling interval in seconds
    STABLE_ERROR_THRESHOLD: float = 10.0  # Percent error threshold for "stable"
    INTER_SPEED_DELAY: float = 2.0  # Seconds to wait between speeds

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Encoder Verification",
            guide_ref="§5.2, §12.2",
            purpose="""
Verify encoder direction polarity, velocity accuracy, and DPLL
effectiveness across multiple speed ranges.

Tests at 100 RPM (DPLL-sensitive), 500 RPM (mid-range), and
1500 RPM (high-speed) to characterize encoder behavior and
identify configuration issues.""",

            prerequisites=[
                "LinuxCNC loaded and machine power ON",
                "Spindle area clear",
                "DPLL should be configured for best results",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle runs at 100 RPM (tests DPLL sensitivity)",
                "3. Spindle runs at 500 RPM (mid-range test)",
                "4. Spindle runs at 1500 RPM (high-speed test)",
                "5. At each speed, feedback is sampled for 2 seconds after stabilization",
                "6. Noise, accuracy, and polarity are analyzed",
            ],

            expected_results=[
                "Feedback positive at all speeds (correct polarity)",
                "Speed error < 5% at each setpoint",
                "Low-speed noise < 20 RPM peak-to-peak",
                "High-speed noise < 10 RPM peak-to-peak",
            ],

            troubleshooting=[
                "NEGATIVE feedback: Encoder polarity REVERSED",
                "  -> Fix: Negate ENCODER_SCALE or swap A/B wires",
                "High low-speed noise: DPLL not configured",
                "  -> Fix: Set encoder.timer-number=1, dpll.01.timer-us=-100",
                "Large speed error: Wrong ENCODER_SCALE value",
                "  -> Fix: Verify 4096 for 1024 PPR encoder",
                "No feedback: Encoder not connected or faulty",
                "  -> Fix: Check wiring and encoder power",
            ],

            safety_notes=[
                "Test runs up to 1500 RPM",
                "Keep clear of spindle during test",
                "Spindle stops automatically between speeds",
            ]
        )

    def run(self) -> None:
        """Start encoder verification in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self) -> None:
        """Execute encoder verification sequence."""
        self.log_header()
        results: List[Dict[str, float]] = []

        for i, (target, desc) in enumerate(self.SPEEDS):
            if self.test_abort:
                break

            progress = (i / len(self.SPEEDS)) * 80
            self.update_progress(progress, f"Testing {target} RPM...")

            self.log_result(f"\nTesting {target} RPM ({desc})...")

            # Start spindle
            self.hal.send_mdi(f"M3 S{target}")

            # Wait for spindle to ramp up and stabilize
            stabilized = self._wait_for_stable_speed(target)
            if not stabilized:
                self.log_result(
                    f"  [WARN] Spindle did not stabilize at {target} RPM within timeout"
                )
                self.hal.send_mdi("M5")
                time.sleep(self.INTER_SPEED_DELAY)
                continue

            # Sample feedback
            _, samples = self.sample_signal(
                MONITOR_PINS["feedback"], self.SAMPLE_DURATION, self.SAMPLE_INTERVAL
            )
            if not samples:
                self.log_result("  [FAIL] No samples collected")
                self.hal.send_mdi("M5")
                time.sleep(self.INTER_SPEED_DELAY)
                continue

            avg = sum(samples) / len(samples)
            noise = max(samples) - min(samples)
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0.0

            results.append({
                "target": float(target),
                "avg": avg,
                "noise": noise,
                "error_pct": error_pct,
            })

            # Check for no feedback (encoder disconnected/faulty)
            if abs(avg) < 1.0:
                self.log_result(f"  [FAIL] NO FEEDBACK detected (~0 RPM)")
                self.log_result("    -> Check encoder connection/power")
            elif avg < 0:
                self.log_result(f"  [FAIL] NEGATIVE feedback: {avg:.1f} RPM")
                self.log_result("    -> Encoder polarity REVERSED")
            else:
                self.log_result(f"  Actual: {avg:.1f} RPM (error: {error_pct:.1f}%)")
                self.log_result(f"  Noise: +/-{noise/2:.1f} RPM (peak-to-peak: {noise:.1f})")

            # Stop spindle between tests
            self.hal.send_mdi("M5")
            time.sleep(self.INTER_SPEED_DELAY)

        self.update_progress(90, "Analyzing results...")

        if not results:
            self.log_result("\n[FAIL] No valid results collected")
            self.end_test()
            return

        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")

        # Polarity check
        if any(r["avg"] < 0 for r in results):
            self.log_result("  [FAIL] NEGATIVE FEEDBACK detected")
            self.log_result("    -> Encoder polarity REVERSED")
            self.log_result("    -> Fix: Negate ENCODER_SCALE or swap A/B wires")
        else:
            self.log_result("  [OK] Encoder polarity CORRECT (positive in M3)")

        # Accuracy check
        max_error = max(r["error_pct"] for r in results)
        if max_error > 10:
            self.log_result(f"  [FAIL] High speed error (max {max_error:.1f}%)")
            self.log_result("    -> Check ENCODER_SCALE matches actual PPR")
        elif max_error > 5:
            self.log_result(f"  [WARN] Moderate speed error (max {max_error:.1f}%)")
        else:
            self.log_result(f"  [OK] Speed accuracy OK (max error {max_error:.1f}%)")

        # Noise checks for each speed
        for r in results:
            target_rpm = int(r["target"])
            # Low-speed gets more noise tolerance
            noise_threshold = TARGETS.noise_good if target_rpm <= 100 else TARGETS.noise_excellent
            if r["noise"] > noise_threshold * 2:
                self.log_result(
                    f"  [WARN] HIGH NOISE at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)"
                )
                if target_rpm <= 100:
                    self.log_result("    -> Check DPLL configuration (Guide §5.4)")
            elif r["noise"] > noise_threshold:
                self.log_result(
                    f"  [WARN] Moderate noise at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)"
                )
            else:
                self.log_result(f"  [OK] Noise OK at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)")

        self.update_progress(100, "Complete")
        self.log_footer("COMPLETE")
        self.end_test()

    def _wait_for_stable_speed(self, target: int) -> bool:
        """
        Wait for spindle speed to stabilize within threshold.

        Args:
            target: Target RPM to wait for.

        Returns:
            True if stabilized within timeout, False otherwise.
        """
        start_time = time.time()
        while time.time() - start_time < self.RAMP_UP_TIMEOUT:
            if self.test_abort:
                return False

            _, samples = self.sample_signal(
                MONITOR_PINS["feedback"], 0.5, self.SAMPLE_INTERVAL
            )
            if not samples:
                time.sleep(self.RAMP_UP_CHECK_INTERVAL)
                continue

            avg = sum(samples) / len(samples)
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0.0
            if error_pct < self.STABLE_ERROR_THRESHOLD:
                return True

            time.sleep(self.RAMP_UP_CHECK_INTERVAL)
        return False
