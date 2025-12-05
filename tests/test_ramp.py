"""
Full Ramp Test

Tests complete 0 -> Target -> 0 RPM cycle with dynamic monitoring.
"""

import time
from tests.base import BaseTest, ProcedureDescription


class RampTest(BaseTest):
    """Full ramp test (0->max->0) with phase analysis."""

    TEST_NAME = "Full Ramp Test"

    # Configuration
    TARGET_RPM = 1800
    HOLD_TIME = 3.0       # Seconds to hold at max speed
    TIMEOUT_RAMP = 10.0   # Max seconds to wait for ramp before failing
    TOLERANCE_RPM = 50    # RPM range considered "at speed"

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Full Ramp Test",
            guide_ref="",
            purpose=f"""
Test the complete speed range from 0 to {cls.TARGET_RPM} RPM
and back to 0. This differentiates between acceleration tracking
(Feed Forward) and steady-state stability (PID).

Phases analyzed:
1. Acceleration: Checks FF1 tuning and VFD ramp matching.
2. Steady State: Checks P/I gain and noise/oscillation.
3. Deceleration: Checks braking behavior and following error.""",

            prerequisites=[
                "Basic Direction Test passed",
                "Encoder feedback verified",
                f"Spindle safe for {cls.TARGET_RPM} RPM",
            ],

            procedure=[
                "1. Click 'Run Test' to begin",
                f"2. System commands {cls.TARGET_RPM} RPM",
                "3. Waits for spindle to reach speed (Dynamic)",
                "4. Holds for stability check",
                "5. Commands 0 RPM and monitors stop",
            ],

            expected_results=[
                f"Peak RPM reaches {cls.TARGET_RPM} +/- {cls.TOLERANCE_RPM}",
                "Steady state jitter < 20 RPM",
                "No over-current trips on VFD",
                "Accel/Decel error < 100 RPM",
            ],

            troubleshooting=[
                "High Error during Ramps:",
                "  -> Adjust [SPINDLE] FF1 in INI file.",
                "  -> Ensure MAX_ACCELERATION matches VFD setting.",
                "Oscillation at Steady Speed:",
                "  -> Reduce P gain, increase D gain slightly.",
                "  -> Check belt tension.",
                "Never reaches target speed:",
                "  -> Check MAX_OUTPUT or OUTPUT_SCALE in INI.",
                "  -> Check VFD max frequency settings.",
            ],

            safety_notes=[
                f"Test runs at HIGH speed ({cls.TARGET_RPM} RPM)",
                "Ensure chuck key is removed",
                "Ensure workpiece/chuck is balanced",
                "Be ready to hit E-STOP",
            ]
        )

    def run(self):
        """Start full ramp test in background thread."""
        if not self.start_test():
            return

        try:
            self.run_sequence(self._sequence)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.log_result(f"Error during test: {exc}")
        finally:
            self.hal.send_mdi("M5")
            self.end_test()

    def _sequence(self):
        """Execute full ramp test."""
        self.log_header(f"FULL RAMP: 0 -> {self.TARGET_RPM} -> 0 RPM")

        test_data = {
            'accel': [],
            'steady': [],
            'decel': [],
        }

        # --- PHASE 1: ACCELERATION ---
        self.log_result(f"Commanding M3 S{self.TARGET_RPM}...")
        self.hal.send_mdi(f"M3 S{self.TARGET_RPM}")

        start_time = time.monotonic()
        ramp_complete = False

        while (time.monotonic() - start_time) < self.TIMEOUT_RAMP:
            if self.test_abort:
                return

            now = time.monotonic()
            t_delta = now - start_time
            values = self.hal.get_all_values()

            test_data['accel'].append({
                'time': t_delta,
                'cmd': values.get('cmd_limited', 0),
                'fb': values.get('feedback', 0),
            })

            if values.get('feedback', 0) >= (self.TARGET_RPM - self.TOLERANCE_RPM):
                ramp_complete = True
                self.log_result(f"Reached target in {t_delta:.2f}s")
                break

            progress = (t_delta / self.TIMEOUT_RAMP) * 30
            self.update_progress(progress, f"Accel: {values.get('feedback', 0):.0f} RPM")
            time.sleep(0.05)

        if not ramp_complete:
            self.log_result("TIMED OUT waiting for target speed.")
            return

        # --- PHASE 2: STEADY STATE ---
        self.log_result(f"Holding {self.HOLD_TIME}s for stability check...")
        hold_start = time.monotonic()

        while (time.monotonic() - hold_start) < self.HOLD_TIME:
            if self.test_abort:
                return

            now = time.monotonic()
            values = self.hal.get_all_values()
            test_data['steady'].append({
                'cmd': values.get('cmd_limited', 0),
                'fb': values.get('feedback', 0),
            })

            hold_progress = 40 + (now - hold_start) * 10
            self.update_progress(hold_progress, f"Holding: {values.get('feedback', 0):.0f} RPM")
            time.sleep(0.1)

        # --- PHASE 3: DECELERATION ---
        self.log_result("Commanding Stop (M5)...")
        self.hal.send_mdi("M5")
        decel_start = time.monotonic()
        stop_complete = False

        while (time.monotonic() - decel_start) < self.TIMEOUT_RAMP:
            if self.test_abort:
                return

            now = time.monotonic()
            t_delta = now - decel_start
            values = self.hal.get_all_values()

            test_data['decel'].append({
                'time': t_delta,
                'cmd': values.get('cmd_limited', 0),
                'fb': values.get('feedback', 0),
            })

            if values.get('feedback', 0) < 5:
                stop_complete = True
                self.log_result(f"Stopped in {t_delta:.2f}s")
                break

            decel_progress = 70 + (t_delta / self.TIMEOUT_RAMP) * 25
            self.update_progress(decel_progress, f"Decel: {values.get('feedback', 0):.0f} RPM")
            time.sleep(0.05)

        if not stop_complete:
            self.log_result("TIMED OUT waiting for stop.")
            return

        # --- ANALYSIS ---
        self.update_progress(95, "Analyzing...")
        self._analyze_results(test_data)
        self.update_progress(100, "Done")

    def _analyze_results(self, data):
        """Calculate stats per phase."""

        def get_max_error(phase_data):
            if not phase_data:
                return 0
            return max(abs(d['cmd'] - d['fb']) for d in phase_data)

        accel_err = get_max_error(data['accel'])
        steady_err = get_max_error(data['steady'])
        decel_err = get_max_error(data['decel'])

        avg_steady = (
            sum(d['fb'] for d in data['steady']) / len(data['steady'])
            if data['steady'] else 0
        )

        self.log_result("\n--- DIAGNOSTICS ---")
        self.log_result(f"Accel Max Error:   {accel_err:.0f} RPM")
        self.log_result(f"Decel Max Error:   {decel_err:.0f} RPM")
        self.log_result(f"Steady State Avg:  {avg_steady:.0f} RPM (Error: {steady_err:.0f})")

        failed = False

        if accel_err > 150:
            self.log_result("FAIL: Accel error too high. Increase FF1.")
            failed = True

        if steady_err > 50:
            self.log_result("FAIL: Unstable at top speed. Check P/I terms.")
            failed = True

        if abs(avg_steady - self.TARGET_RPM) > 100:
            self.log_result("FAIL: Did not reach target RPM. Check Output Scale.")
            failed = True

        if not failed:
            self.log_footer("PASS")
            self.log_result("  Spindle tracks well across all phases.")
        else:
            self.log_footer("TUNING REQUIRED")
