"""
Encoder Verification Test (Guide §5.2, §12.2)

Multi-speed encoder accuracy and polarity verification.
"""

import time

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription, TARGETS


class EncoderTest(BaseTest):
    """Encoder verification test (Guide §5.2, §12.2)."""

    TEST_NAME = "Encoder Verification"
    GUIDE_REF = "Guide §5.2, §12.2"

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
                "5. At each speed, feedback is sampled for 2 seconds",
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
            ],

            safety_notes=[
                "Test runs up to 1500 RPM",
                "Keep clear of spindle during test",
                "Spindle stops automatically between speeds",
            ]
        )

    def run(self):
        """Start encoder verification in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute encoder verification."""
        self.log_header()

        speeds = [
            (100, "Low speed - DPLL sensitive"),
            (500, "Mid speed"),
            (1500, "High speed")
        ]
        results = []

        for i, (target, desc) in enumerate(speeds):
            if self.test_abort:
                break

            progress = (i / len(speeds)) * 80
            self.update_progress(progress, f"Testing {target} RPM...")

            self.log_result(f"\nTesting {target} RPM ({desc})...")
            self.hal.send_mdi(f"M3 S{target}")
            time.sleep(3.5)

            _, samples = self.sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)

            if not samples:
                self.log_result(f"   [FAIL] No samples collected")
                continue

            avg = sum(samples) / len(samples)
            noise = max(samples) - min(samples)
            error_pct = abs(avg - target) / target * 100 if target > 0 else 0

            results.append({
                'target': target,
                'avg': avg,
                'noise': noise,
                'error_pct': error_pct
            })

            if avg < 0:
                self.log_result(f"   [FAIL] NEGATIVE feedback: {avg:.1f} RPM")
                self.log_result(f"     -> Encoder polarity REVERSED")
            else:
                self.log_result(f"   Actual: {avg:.1f} RPM (error: {error_pct:.1f}%)")
                self.log_result(f"   Noise: +/-{noise/2:.1f} RPM (peak-to-peak: {noise:.1f})")

        self.hal.send_mdi("M5")
        self.update_progress(90, "Analyzing results...")

        if not results:
            self.log_result("\n[FAIL] No valid results collected")
            self.end_test()
            return

        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")

        # Check low-speed noise (DPLL indicator)
        low_result = results[0] if results else None
        if low_result:
            if low_result['noise'] > TARGETS.noise_good:
                self.log_result(f"  [WARN] HIGH LOW-SPEED NOISE ({low_result['noise']:.0f} RPM)")
                self.log_result("    -> Check DPLL configuration (Guide §5.4)")
            elif low_result['noise'] > TARGETS.noise_excellent:
                self.log_result(f"  [WARN] Moderate low-speed noise ({low_result['noise']:.0f} RPM)")
            else:
                self.log_result(f"  [OK] Low-speed noise OK ({low_result['noise']:.0f} RPM)")

        # Check polarity
        for r in results:
            if r['avg'] < 0:
                self.log_result(f"  [FAIL] NEGATIVE FEEDBACK at {r['target']} RPM")
                self.log_result("    -> Encoder polarity REVERSED")
                self.log_result("    -> Fix: Negate ENCODER_SCALE or swap A/B wires")
                break
        else:
            self.log_result("  [OK] Encoder polarity CORRECT (positive in M3)")

        # Check accuracy
        high_error = max(r['error_pct'] for r in results)
        if high_error > 10:
            self.log_result(f"  [WARN] High speed error ({high_error:.1f}%)")
            self.log_result("    -> Check ENCODER_SCALE matches actual PPR")
        elif high_error > 5:
            self.log_result(f"  [WARN] Moderate speed error ({high_error:.1f}%)")
        else:
            self.log_result(f"  [OK] Speed accuracy OK (max error {high_error:.1f}%)")

        self.update_progress(100, "Complete")
        self.log_footer("COMPLETE")
        self.end_test()
