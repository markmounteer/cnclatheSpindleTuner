"""
Reverse PID Test (Guide §6.3)

CRITICAL SAFETY TEST - Verifies reverse (M4) operation and ABS component.
"""

import importlib.util
import time

_HAS_TKINTER = importlib.util.find_spec("tkinter") is not None
if _HAS_TKINTER:
    from tkinter import messagebox
else:
    messagebox = None

from config import MONITOR_PINS
from tests.base import BaseTest, ProcedureDescription


class ReverseTest(BaseTest):
    """Reverse safety test (Guide §6.3) with active safety monitoring."""

    TEST_NAME = "Reverse PID Test"
    GUIDE_REF = "Guide §6.3"

    # Configuration
    TARGET_RPM = 500
    # If speed hits this, we kill it immediately (50% overspeed)
    SAFETY_THRESHOLD = 750
    TEST_DURATION = 4.0  # Seconds to run

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Reverse PID Test (M4)",
            guide_ref="§6.3",
            purpose="""
CRITICAL SAFETY TEST for reverse (M4) spindle operation.

Verifies that:
1. Encoder reads NEGATIVE when spinning reverse
2. ABS component converts this to POSITIVE for the PID
3. PID loop remains stable

ACTIVE SOFTWARE MONITORING detects runaway (>750 RPM) and issues M5 automatically.""",

            prerequisites=[
                "Forward PID Test completed successfully",
                "E-stop tested and functional",
                "Hand ready on E-stop during entire test",
            ],

            procedure=[
                "1. Click 'Run Test' - safety confirmation required",
                "2. Spindle starts reverse at 500 RPM (M4 S500)",
                "3. System monitors for runaway (>750 RPM) and auto-stops if detected",
                "4. After ~4 seconds, readings are sampled",
                "5. Spindle stops",
            ],

            expected_results=[
                "Raw feedback: NEGATIVE (around -500 RPM)",
                "ABS feedback: POSITIVE (around +500 RPM)",
                "PID feedback: POSITIVE (around +500 RPM)",
                "No runaway detected by software monitor",
            ],

            troubleshooting=[
                "Raw feedback POSITIVE in reverse:",
                "  -> Encoder polarity REVERSED",
                "  -> Fix: Negate ENCODER_SCALE or swap A/B",
                "ABS feedback NEGATIVE or near zero:",
                "  -> ABS component missing or miswired",
                "  -> Check custom.hal for abs component",
                "PID feedback NEGATIVE while ABS is positive:",
                "  -> PID output likely inverted (double-negative scenario)",
                "  -> Verify PID output polarity and encoder scale",
                "RUNAWAY (speed keeps increasing):",
                "  -> Software issues M5, still HIT E-STOP IMMEDIATELY",
                "  -> Fix ABS component before operating",
            ],

            safety_notes=[
                ">>> CRITICAL SAFETY TEST <<<",
                "Software monitoring is a backup. KEEP HAND ON PHYSICAL E-STOP.",
                "Lower TARGET_RPM/SAFETY_THRESHOLD if needed for your lathe",
            ]
        )

    def run(self):
        """Start reverse test with safety confirmation."""
        if not self.start_test():
            return

        # Safety confirmation required
        if _HAS_TKINTER and not messagebox.askyesno(
            "Reverse Safety Test",
            f"This test runs M4 at {self.TARGET_RPM} RPM.\n\n"
            ">>> KEEP HAND ON E-STOP! <<<\n\n"
            "The software will attempt to auto-stop on runaway,\n"
            "but you must be ready to hit E-Stop.\n\n"
            "Continue?"):
            self.end_test()
            return

        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute reverse safety test with active monitoring."""
        self.log_header()
        self.log_result(">>> ACTIVE SAFETY MONITORING ENABLED <<<")
        self.update_progress(0, "Initializing...")

        # 1. Start Spindle
        self.hal.send_mdi(f"M4 S{self.TARGET_RPM}")
        self.log_result(f"\nCommanded M4 S{self.TARGET_RPM}...")

        # 2. Monitor Loop (Active Safety)
        start_time = time.time()
        runaway_detected = False

        while (time.time() - start_time) < self.TEST_DURATION:
            # Check abort flag (User clicked Stop button)
            if self.test_abort:
                self.hal.send_mdi("M5")
                self.end_test()
                return

            # Get current absolute speed for safety check
            raw_vel = self.hal.get_pin_value(
                MONITOR_PINS.get('feedback_raw', 'spindle-vel-fb-rpm'))
            current_speed = abs(raw_vel)

            # SAFETY CHECK: Runaway Detection
            if current_speed > self.SAFETY_THRESHOLD:
                self.hal.send_mdi("M5")  # KILL SPINDLE
                runaway_detected = True
                self.log_result("!!! EMERGENCY STOP TRIGGERED BY SOFTWARE !!!")
                self.log_result(
                    f"Speed {current_speed:.0f} exceeded limit {self.SAFETY_THRESHOLD}")
                break

            # Update UI gently
            elapsed = time.time() - start_time
            progress = (elapsed / self.TEST_DURATION) * 80
            self.update_progress(int(progress), f"Running... {current_speed:.0f} RPM")

            # Non-blocking sleep
            time.sleep(0.1)

        # 3. Capture Data (or analyze crash data)
        self.update_progress(90, "Sampling signals...")

        fb_raw = self.hal.get_pin_value(
            MONITOR_PINS.get('feedback_raw', 'spindle-vel-fb-rpm'))
        fb_abs = self.hal.get_pin_value(MONITOR_PINS['feedback_abs'])
        pid_fb = self.hal.get_pin_value(MONITOR_PINS['feedback'])

        # Stop Spindle (if not already stopped by safety check)
        self.hal.send_mdi("M5")

        # 4. Report Results
        self.log_result("\nFinal Readings:")
        self.log_result(f"  Raw feedback: {fb_raw:.1f} RPM (Target: Negative)")
        self.log_result(f"  ABS feedback: {fb_abs:.1f} RPM (Target: Positive)")
        self.log_result(f"  PID feedback: {pid_fb:.1f} RPM (Target: Positive)")

        # 5. Analysis
        self.update_progress(100, "Complete")

        if runaway_detected:
            self.log_footer("FAIL - RUNAWAY")
            self.log_result("CRITICAL: The spindle accelerated out of control.")
            self.log_result("CAUSE: The PID Controller received NEGATIVE feedback.")
            self.log_result("FIX: Ensure the 'abs' component is installed and linked in HAL.")
            self.log_result("     (net spindle-vel-fb-rpm => abs.0.in)")
            self.log_result("     (net spindle-abs-vel <= abs.0.out)")
            self.end_test()
            return

        raw_is_negative = fb_raw < -50
        abs_is_positive = fb_abs > 50
        pid_is_positive = pid_fb > 50
        pid_is_negative = pid_fb < -50

        if raw_is_negative and abs_is_positive and pid_is_positive:
            self.log_footer("PASS")
            self.log_result("  System correctly handles reverse direction.")
            self.log_result("  ABS component is functioning.")

        elif abs_is_positive and pid_is_negative:
            self.log_footer("FAIL - DOUBLE NEGATIVE")
            self.log_result("  ABS output was positive, but PID feedback went negative.")
            self.log_result(
                "  Encoder scale or PID output polarity may both be inverted, masking runaway risk.")
            self.log_result("  -> Verify encoder scale sign and PID output direction.")

        elif not raw_is_negative:
            self.log_footer("FAIL - POLARITY ERROR")
            self.log_result("  Raw feedback was POSITIVE while spinning reverse.")
            self.log_result("  -> Invert encoder scale (make it negative).")
            self.log_result("  -> Or swap Encoder A/B wires.")

        elif raw_is_negative and not abs_is_positive:
            self.log_footer("FAIL - ABS MISSING")
            self.log_result("  Encoder is negative (Correct), but PID sees negative (Wrong).")
            self.log_result("  PID needs POSITIVE feedback to control speed.")
            self.log_result("  -> Check 'abs' component in custom.hal.")

        else:
            self.log_footer("FAIL - INCONCLUSIVE")
            self.log_result("  Readings were unstable or too low to verify.")

        self.end_test()
