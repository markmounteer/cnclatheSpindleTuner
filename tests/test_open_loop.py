"""
Open Loop Check Test (Guide §6.1)

Measures motor slip with feedforward only (no PID correction).
"""

import time
import threading

from config import MONITOR_PINS, MOTOR_SPECS
from tests.base import BaseTest, TestDescription


class OpenLoopTest(BaseTest):
    """Open loop baseline test (Guide §6.1)."""

    TEST_NAME = "Open Loop Check"
    GUIDE_REF = "Guide §6.1"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Open Loop Check",
            guide_ref="§6.1",
            purpose="""
Temporarily disable PID feedback to measure raw motor slip with
only feedforward (FF0) active. This establishes the baseline
motor behavior before PID tuning begins.

The test reveals the natural motor slip (typically 2-3% for cold
motor, 3-4% for hot motor) which the PID I-term must compensate.""",

            prerequisites=[
                "LinuxCNC loaded and machine power ON",
                "Spindle area clear",
                "Motor at normal operating temperature",
                "Understand that slip varies with motor temperature",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Current P, I, FF0 values are saved",
                "3. P=0, I=0, FF0=1.0 set (pure feedforward)",
                "4. Spindle commanded to 1000 RPM",
                "5. Actual speed measured (should be 950-980 RPM)",
                "6. Slip percentage calculated",
                "7. Original parameters restored",
            ],

            expected_results=[
                "Motor slip: 1.5-5% (normal range)",
                "Cold motor: ~2.7% slip (~973 RPM at 1000 cmd)",
                "Hot motor: ~3.6% slip (~964 RPM at 1000 cmd)",
                "If way off: VFD or encoder scale wrong",
            ],

            troubleshooting=[
                "Slip < 1.5%: Encoder scale too high or VFD offset",
                "Slip > 5%: Motor under load, or encoder scale low",
                "No speed: Check VFD analog input wiring",
                "Erratic speed: Check VFD P0.03 (analog input mode)",
            ],

            safety_notes=[
                "Test runs at 1000 RPM",
                "PID feedback temporarily disabled",
                "Parameters automatically restored after test",
            ]
        )

    def run(self):
        """Start open loop check in background thread."""
        if not self.start_test():
            return
        threading.Thread(target=self._sequence, daemon=True).start()

    def _sequence(self):
        """Execute open loop check."""
        self.log_header()
        self.log_result("Measuring motor slip with FF0 only (no PID correction)")
        self.update_progress(0, "Saving parameters...")

        # Save current parameters
        p_orig = self.hal.get_param('P')
        i_orig = self.hal.get_param('I')
        ff0_orig = self.hal.get_param('FF0')

        self.log_result("\nSetting: P=0, I=0, FF0=1.0...")
        self.update_progress(10, "Setting open-loop mode...")

        self.hal.set_param('P', 0)
        self.hal.set_param('I', 0)
        self.hal.set_param('FF0', 1.0)

        self.hal.send_mdi("M3 S1000")
        self.log_result("Commanding 1000 RPM...")
        self.update_progress(20, "Accelerating to 1000 RPM...")

        time.sleep(4)

        if self.test_abort:
            self.hal.send_mdi("M5")
            self.hal.set_param('P', p_orig)
            self.hal.set_param('I', i_orig)
            self.hal.set_param('FF0', ff0_orig)
            self.end_test()
            return

        self.update_progress(60, "Sampling feedback...")

        _, fb_samples = self.sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
        cmd = self.hal.get_pin_value(MONITOR_PINS['cmd_limited'])

        self.hal.send_mdi("M5")
        self.update_progress(80, "Calculating slip...")

        if fb_samples:
            fb = sum(fb_samples) / len(fb_samples)
            fb_noise = max(fb_samples) - min(fb_samples)
        else:
            fb = 0
            fb_noise = 0

        slip = ((cmd - fb) / cmd * 100) if cmd > 0 else 0
        expected_slip = MOTOR_SPECS.get('cold_slip_pct', 2.7)

        self.log_result(f"\nResults:")
        self.log_result(f"  Command: {cmd:.0f} RPM")
        self.log_result(f"  Feedback: {fb:.0f} RPM (noise: +/-{fb_noise/2:.1f})")
        self.log_result(f"  Measured slip: {slip:.1f}%")
        self.log_result(f"  Expected cold slip: {expected_slip:.1f}%")

        if 1.5 <= slip <= 5.0:
            self.log_result("\n[PASS] Slip within normal range (1.5-5%)")
            self.log_result("  FF0=1.0 is appropriate baseline")
        elif slip < 1.5:
            self.log_result(f"\n[WARN] LOW SLIP: {slip:.1f}%")
            self.log_result("  Possible causes:")
            self.log_result("  - Encoder scale too high")
            self.log_result("  - VFD output frequency offset")
        elif slip > 5.0:
            self.log_result(f"\n[WARN] HIGH SLIP: {slip:.1f}%")
            self.log_result("  Possible causes:")
            self.log_result("  - Motor under load")
            self.log_result("  - Encoder scale too low")
            self.log_result("  - Motor overheating")

        # Restore parameters
        self.update_progress(90, "Restoring parameters...")
        self.hal.set_param('P', p_orig)
        self.hal.set_param('I', i_orig)
        self.hal.set_param('FF0', ff0_orig)
        self.log_result("\nParameters restored.")

        self.update_progress(100, "Complete")
        self.log_footer("COMPLETE")
        self.end_test()
