"""
Reverse PID Test (Guide §6.3)

CRITICAL SAFETY TEST - Verifies reverse (M4) operation and ABS component.
"""

import time

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None
    _HAS_TKINTER = False

from config import MONITOR_PINS
from tests.base import BaseTest, TestDescription


class ReverseTest(BaseTest):
    """Reverse safety test (Guide §6.3)."""

    TEST_NAME = "Reverse PID Test"
    GUIDE_REF = "Guide §6.3"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Reverse PID Test (M4)",
            guide_ref="§6.3",
            purpose="""
CRITICAL SAFETY TEST for reverse (M4) spindle operation.

Verifies that:
1. Encoder reads NEGATIVE when spinning reverse
2. ABS component outputs POSITIVE magnitude
3. PID receives positive feedback for stable control

If ABS component is broken, M4 will cause RUNAWAY - the PID sees
negative feedback and increases output trying to go "faster".""",

            prerequisites=[
                "Forward PID Test completed successfully",
                "E-stop tested and functional",
                "Hand ready on E-stop during entire test",
            ],

            procedure=[
                "1. Click 'Run Test' - safety confirmation required",
                "2. KEEP HAND ON E-STOP THROUGHOUT TEST",
                "3. Spindle starts reverse at 500 RPM (M4 S500)",
                "4. Raw feedback should be NEGATIVE (~-500)",
                "5. ABS feedback should be POSITIVE (~500)",
                "6. PID feedback should be POSITIVE (~500)",
                "7. Any runaway -> HIT E-STOP IMMEDIATELY",
            ],

            expected_results=[
                "Raw feedback: NEGATIVE (around -500 RPM)",
                "ABS feedback: POSITIVE (around +500 RPM)",
                "PID feedback: POSITIVE (around +500 RPM)",
                "Speed stable, not accelerating uncontrolled",
            ],

            troubleshooting=[
                "Raw feedback POSITIVE in reverse:",
                "  -> Encoder polarity REVERSED",
                "  -> Fix: Negate ENCODER_SCALE or swap A/B",
                "ABS feedback NEGATIVE or near zero:",
                "  -> ABS component missing or miswired",
                "  -> Check custom.hal for abs component",
                "RUNAWAY (speed keeps increasing):",
                "  -> HIT E-STOP IMMEDIATELY",
                "  -> Fix ABS component before operating",
            ],

            safety_notes=[
                ">>> CRITICAL SAFETY TEST <<<",
                "KEEP HAND ON E-STOP AT ALL TIMES",
                "If spindle accelerates uncontrolled: HIT E-STOP",
                "Do NOT operate M4 until this test passes",
                "Test runs at low speed (500 RPM) for safety",
            ]
        )

    def run(self):
        """Start reverse test with safety confirmation."""
        if not self.start_test():
            return

        # Safety confirmation required
        if not messagebox.askyesno(
            "Reverse Safety Test",
            "This test runs spindle in REVERSE (M4).\n\n"
            ">>> KEEP HAND ON E-STOP! <<<\n\n"
            "If spindle accelerates uncontrolled,\n"
            "HIT E-STOP IMMEDIATELY.\n\n"
            "Continue?"):
            self.end_test()
            return

        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute reverse safety test."""
        self.log_header()
        self.log_result(">>> CRITICAL SAFETY TEST <<<")
        self.log_result(">>> KEEP HAND ON E-STOP <<<")
        self.update_progress(0, "Starting reverse test...")

        self.hal.send_mdi("M4 S500")
        self.log_result("\nStarting M4 S500 (reverse)...")
        self.update_progress(20, "Running reverse...")

        time.sleep(3.5)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        self.update_progress(60, "Sampling signals...")

        fb_raw = self.hal.get_pin_value(
            MONITOR_PINS.get('feedback_raw', 'spindle-vel-fb-rpm'))
        fb_abs = self.hal.get_pin_value(MONITOR_PINS['feedback_abs'])
        pid_fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        at_speed = self.hal.get_pin_value(MONITOR_PINS['at_speed'])

        self.hal.send_mdi("M5")
        self.update_progress(80, "Analyzing results...")

        self.log_result(f"\nSignal Readings:")
        self.log_result(f"  Raw feedback: {fb_raw:.1f} RPM (expect NEGATIVE)")
        self.log_result(f"  ABS feedback: {fb_abs:.1f} RPM (expect POSITIVE)")
        self.log_result(f"  PID feedback: {pid_fb:.1f} RPM (expect POSITIVE)")
        self.log_result(f"  At-speed: {'YES' if at_speed > 0.5 else 'NO'}")

        self.update_progress(100, "Complete")

        if fb_raw < -100 and fb_abs > 100 and pid_fb > 100:
            self.log_footer("PASS")
            self.log_result("  Encoder polarity: CORRECT")
            self.log_result("  ABS component: WORKING")
            self.log_result("  PID sees positive feedback for control")
        elif fb_raw > 0:
            self.log_footer("FAIL - POLARITY ERROR")
            self.log_result("  Raw feedback should be NEGATIVE in reverse")
            self.log_result("  -> Encoder polarity is REVERSED")
            self.log_result("  -> Fix: Negate ENCODER_SCALE or swap A/B")
        elif fb_abs < 100:
            self.log_footer("FAIL - ABS COMPONENT ISSUE")
            self.log_result("  ABS feedback should be positive magnitude")
            self.log_result("  -> Check ABS component in custom.hal")
        else:
            self.log_footer("CHECK SIGNALS")

        self.end_test()
