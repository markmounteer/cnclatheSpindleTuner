"""
Open Loop Check Test (Guide §6.1)

Measures motor slip with feedforward only (no PID correction).
"""

import time

from config import MONITOR_PINS, MOTOR_SPECS
from tests.base import BaseTest, ProcedureDescription


class OpenLoopTest(BaseTest):
    """Open loop baseline test (Guide §6.1)."""

    TEST_NAME = "Open Loop Check"
    GUIDE_REF = "Guide §6.1"

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
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
                "2. Current PID parameters (P, I, D, FF0, FF1, FF2) are saved",
                "3. P=0, I=0, D=0, FF1=0, FF2=0, FF0=1.0 set (pure feedforward)",
                "4. Spindle commanded to 1000 RPM",
                "5. Actual speed measured (should be 950-980 RPM)",
                "6. Slip percentage calculated",
                "7. Original parameters restored automatically",
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
                "Parameters automatically restored even on abort",
            ]
        )

    def run(self):
        """Start open loop check in background thread."""
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute open loop check."""
        self.log_header()
        self.log_result("Measuring motor slip with FF0 only (no PID correction)")

        # Storage for restoring later
        saved_params = {}
        params_to_save = ['P', 'I', 'D', 'FF0', 'FF1', 'FF2']

        try:
            # --- 1. Save State ---
            self.update_progress(0, "Saving parameters...")
            for p in params_to_save:
                saved_params[p] = self.hal.get_param(p)

            # --- 2. Setup Open Loop ---
            self.log_result("\nIsolating Feedforward (Setting P=0, I=0, D=0, FF0=1.0)...")
            self.update_progress(10, "Setting open-loop mode...")

            # Zero out all PID terms for true open-loop behavior
            self.hal.set_param('P', 0)
            self.hal.set_param('I', 0)
            self.hal.set_param('D', 0)
            self.hal.set_param('FF1', 0)
            self.hal.set_param('FF2', 0)
            # Set pure Feedforward
            self.hal.set_param('FF0', 1.0)

            # --- 3. Run Motor ---
            self.hal.send_mdi("M3 S1000")
            self.log_result("Commanding 1000 RPM...")
            self.update_progress(20, "Accelerating to 1000 RPM...")

            # Wait for run-up with abort checking
            for i in range(40):  # 4 seconds total
                if self.test_abort:
                    raise InterruptedError("Test aborted by user")
                time.sleep(0.1)

            # --- 4. Sample Data ---
            self.update_progress(60, "Sampling feedback...")
            if self.test_abort:
                raise InterruptedError("Test aborted by user")

            _, fb_samples = self.sample_signal(MONITOR_PINS['feedback'], 2.0, 0.1)
            cmd = self.hal.get_pin_value(MONITOR_PINS['cmd_limited'])

            # --- 5. Analysis ---
            self.update_progress(80, "Calculating slip...")

            if fb_samples:
                fb = sum(fb_samples) / len(fb_samples)
                fb_noise = max(fb_samples) - min(fb_samples)
            else:
                fb = 0
                fb_noise = 0

            # Use abs() to handle cases where encoder might be inverted relative to command
            # slip = (command - actual) / command
            slip = ((abs(cmd) - abs(fb)) / abs(cmd) * 100) if abs(cmd) > 0 else 0
            expected_slip = MOTOR_SPECS.get('cold_slip_pct', 2.7)

            self.log_result("\nResults:")
            self.log_result(f"  Command: {cmd:.0f} RPM")
            self.log_result(f"  Feedback: {fb:.0f} RPM (noise: +/-{fb_noise/2:.1f})")
            self.log_result(f"  Measured slip: {slip:.1f}%")
            self.log_result(f"  Expected cold slip: {expected_slip:.1f}%")

            # Logic checks
            if 1.5 <= slip <= 5.0:
                self.log_result("\n[PASS] Slip within normal range (1.5-5%)")
                self.log_result("  FF0=1.0 is appropriate baseline")
            elif slip < 1.5:
                self.log_result(f"\n[WARN] LOW SLIP: {slip:.1f}%")
                self.log_result("  Possible causes:")
                self.log_result("  - Encoder scale too high (reading faster than reality)")
                self.log_result("  - VFD output frequency offset (running faster than 10V request)")
            elif slip > 5.0:
                self.log_result(f"\n[WARN] HIGH SLIP: {slip:.1f}%")
                self.log_result("  Possible causes:")
                self.log_result("  - Motor under significant load (spindle drag?)")
                self.log_result("  - Encoder scale too low")
                self.log_result("  - VFD failing to reach full frequency")

        except InterruptedError:
            self.log_result("\n[ABORT] Test interrupted.")
        except Exception as e:
            self.log_result(f"\n[ERROR] Unexpected error: {e}")
        finally:
            # --- 6. Cleanup & Restore ---
            # This block runs NO MATTER WHAT happens above
            self.update_progress(90, "Restoring parameters...")
            self.hal.send_mdi("M5")  # Stop spindle

            # Restore only if we successfully saved them
            if saved_params:
                for p, val in saved_params.items():
                    self.hal.set_param(p, val)
                self.log_result("\nOriginal PID parameters restored.")
            else:
                self.log_result("\n[WARN] Could not restore parameters (save failed).")

            self.update_progress(100, "Complete")
            self.log_footer("COMPLETE")
            self.end_test()
