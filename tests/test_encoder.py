"""
Encoder Verification Test (Guide §5.2, §12.2)

Multi-speed encoder accuracy and polarity verification.
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Tuple

from config import MONITOR_PINS
from .base import BaseTest, ProcedureDescription, TARGETS


class EncoderTest(BaseTest):
    """Encoder verification test (Guide §5.2, §12.2)."""

    TEST_NAME = "Encoder Verification"
    GUIDE_REF = "Guide §5.2, §12.2"

    SPEEDS: List[Tuple[int, str]] = [
        (100, "Low speed - DPLL sensitive"),
        (500, "Mid speed"),
        (1500, "High speed"),
    ]

    RAMP_UP_TIMEOUT: float = 10.0
    RAMP_UP_CHECK_INTERVAL: float = 0.5
    SAMPLE_DURATION: float = 2.0
    SAMPLE_INTERVAL: float = 0.1
    STABLE_ERROR_THRESHOLD: float = 10.0  # percent
    INTER_SPEED_DELAY: float = 2.0

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Encoder Verification",
            guide_ref="§5.2, §12.2",
            purpose=(
                "Verify encoder direction polarity, velocity accuracy, and DPLL\n"
                "effectiveness across multiple speed ranges.\n\n"
                "Tests at 100 RPM (DPLL-sensitive), 500 RPM (mid-range), and\n"
                "1500 RPM (high-speed) to characterize encoder behavior and\n"
                "identify configuration issues."
            ),
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
            ],
        )

    def run(self) -> None:
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self) -> None:
        self.log_header()
        feedback_pin = MONITOR_PINS["feedback"]

        results: List[Dict[str, float]] = []
        any_negative = False
        any_no_feedback = False

        for i, (target, desc) in enumerate(self.SPEEDS):
            if self.check_abort():
                self.log_footer("ABORTED")
                return

            progress = (i / len(self.SPEEDS)) * 80
            self.update_progress(progress, f"Testing {target} RPM...")
            self.log_result(f"\nTesting {target} RPM ({desc})...")

            self.hal.send_mdi(f"M3 S{target}")

            if not self._wait_for_stable_speed(feedback_pin, target):
                self.log_result(f"  [WARN] Spindle did not stabilize at {target} RPM within timeout")
                self.hal.send_mdi("M5")
                if not self.sleep(self.INTER_SPEED_DELAY):
                    self.log_footer("ABORTED")
                    return
                continue

            _, samples = self.sample_signal(feedback_pin, self.SAMPLE_DURATION, self.SAMPLE_INTERVAL)
            samples = [float(s) for s in samples if math.isfinite(float(s))]

            if not samples:
                self.log_result("  [FAIL] No valid samples collected")
                self.hal.send_mdi("M5")
                if not self.sleep(self.INTER_SPEED_DELAY):
                    self.log_footer("ABORTED")
                    return
                continue

            avg = sum(samples) / len(samples)
            noise_pp = max(samples) - min(samples) if len(samples) > 1 else 0.0
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0.0

            results.append({"target": float(target), "avg": float(avg), "noise": float(noise_pp), "error_pct": float(error_pct)})

            if abs(avg) < 1.0:
                any_no_feedback = True
                self.log_result("  [FAIL] NO FEEDBACK detected (~0 RPM)")
                self.log_result("    -> Check encoder connection/power")
            elif avg < 0:
                any_negative = True
                self.log_result(f"  [FAIL] NEGATIVE feedback: {avg:.1f} RPM")
                self.log_result("    -> Encoder polarity REVERSED")
            else:
                self.log_result(f"  Actual: {avg:.1f} RPM (error: {error_pct:.1f}%)")
                self.log_result(f"  Noise: +/-{noise_pp/2:.1f} RPM (peak-to-peak: {noise_pp:.1f})")

            self.hal.send_mdi("M5")
            if not self.sleep(self.INTER_SPEED_DELAY):
                self.log_footer("ABORTED")
                return

        self.update_progress(90, "Analyzing results...")

        if not results:
            self.log_result("\n[FAIL] No valid results collected")
            self.log_footer("FAIL")
            return

        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")

        if any_negative:
            self.log_result("  [FAIL] NEGATIVE FEEDBACK detected")
            self.log_result("    -> Encoder polarity REVERSED")
            self.log_result("    -> Fix: Negate ENCODER_SCALE or swap A/B wires")
        else:
            self.log_result("  [OK] Encoder polarity CORRECT (positive in M3)")

        max_error = max(r["error_pct"] for r in results)
        if max_error > 10:
            self.log_result(f"  [FAIL] High speed error (max {max_error:.1f}%)")
            self.log_result("    -> Check ENCODER_SCALE matches actual PPR")
        elif max_error > 5:
            self.log_result(f"  [WARN] Moderate speed error (max {max_error:.1f}%)")
        else:
            self.log_result(f"  [OK] Speed accuracy OK (max error {max_error:.1f}%)")

        for r in results:
            target_rpm = int(r["target"])
            noise_threshold = TARGETS.noise_good if target_rpm <= 100 else TARGETS.noise_excellent

            if r["noise"] > noise_threshold * 2:
                self.log_result(f"  [WARN] HIGH NOISE at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)")
                if target_rpm <= 100:
                    self.log_result("    -> Check DPLL configuration (Guide §5.4)")
            elif r["noise"] > noise_threshold:
                self.log_result(f"  [WARN] Moderate noise at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)")
            else:
                self.log_result(f"  [OK] Noise OK at {target_rpm} RPM ({r['noise']:.0f} RPM p-p)")

        self.update_progress(100, "Complete")

        if any_no_feedback or any_negative or max_error > 10:
            self.log_footer("COMPLETE (ISSUES FOUND)")
        else:
            self.log_footer("COMPLETE")

    def _wait_for_stable_speed(self, feedback_pin: str, target: int) -> bool:
        """Wait for spindle speed to stabilize within threshold."""
        deadline = time.monotonic() + self.RAMP_UP_TIMEOUT

        while time.monotonic() < deadline:
            if self.check_abort():
                return False

            _, samples = self.sample_signal(feedback_pin, 0.5, self.SAMPLE_INTERVAL)
            samples = [float(s) for s in samples if math.isfinite(float(s))]
            if not samples:
                if not self.sleep(self.RAMP_UP_CHECK_INTERVAL):
                    return False
                continue

            avg = sum(samples) / len(samples)
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0.0
            if error_pct < self.STABLE_ERROR_THRESHOLD:
                return True

            if not self.sleep(self.RAMP_UP_CHECK_INTERVAL):
                return False

        return False
