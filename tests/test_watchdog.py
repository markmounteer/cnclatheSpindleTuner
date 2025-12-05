"""
Mock Watchdog Test (Guide §6.6)

Safe encoder watchdog simulation - MOCK MODE ONLY.
Validates that the software logic correctly handles a loss of encoder signal.

Diagram placeholder:
+--------------------------+
|   Encoder Signal Path    |
| (Mock Fault Injection)   |
+--------------------------+
"""

import time
from typing import Optional

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None
    _HAS_TKINTER = False

from config import MONITOR_PINS
from tests.base import BaseTest, ProcedureDescription


class WatchdogTest(BaseTest):
    """Mock encoder watchdog test (Guide §6.6)."""

    TEST_NAME = "Encoder Watchdog Test"
    GUIDE_REF = "Guide §6.6"

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Encoder Watchdog Test (Mock)",
            guide_ref="§6.6",
            purpose=(
                "Safely test the encoder watchdog behavior using programmatic "
                "fault injection in MOCK MODE ONLY.\n\n"
                "On real hardware (e.g., threading on a lathe), if the encoder signal "
                "is lost while the spindle is turning, the carriage must stop immediately "
                "to prevent crashing into the chuck. The watchdog timer triggers this "
                "E-stop within ~1 second."
            ),
            prerequisites=[
                "System running in MOCK MODE (Strict)",
                "No active E-stop conditions prior to start",
            ],
            procedure=[
                "1. Verify Mock Mode (abort if real hardware)",
                "2. Start mock spindle at 1000 RPM",
                "3. Inject programmatic encoder fault (simulate cable break)",
                "4. Monitor HAL signals for E-stop and Fault flags",
                "5. Clear faults and reset system",
            ],
            expected_results=[
                "Encoder fault flag becomes SET",
                "System triggers E-stop or Motion Inhibit",
                "Spindle command drops to 0",
            ],
            troubleshooting=[
                "Test Fails to Start: Restart application with --mock flag",
                "No Fault Detected: Check `set_mock_fault` implementation in HAL mock",
            ],
            safety_notes=[
                ">>> MOCK MODE ONLY <<<",
                "Do not rely on this test for physical safety validation.",
                "Real hardware validation requires an oscilloscope and physical",
                "disconnection of the encoder index pulse during a dry run.",
            ]
        )

    def run(self) -> None:
        """Start mock watchdog test."""
        # strict safety check
        if not getattr(self.hal, 'is_mock', False):
            self._show_safety_warning()
            self.log_result("SKIPPED: Test attempted on real hardware.")
            return

        if not self.start_test():
            return

        # Wrap sequence in try/finally to ensure cleanup happens
        try:
            self.run_sequence(self._sequence)
        except Exception as exc:  # pragma: no cover - user facing logging
            self.log_result(f"CRITICAL ERROR: {exc}")
        finally:
            self._cleanup_system()
            self.end_test()

    def _sequence(self) -> None:
        """Execute safe mock watchdog test."""
        self.log_header()
        self.log_result("SAFE SIMULATION: No physical disconnection required.")

        # 1. Start Spindle
        self.update_progress(10, "Starting mock spindle...")
        self.hal.send_mdi("M3 S1000")
        self.log_result("-> Commanded M3 S1000")
        time.sleep(2)

        # 2. Baseline
        self.update_progress(30, "Reading baseline...")
        fb_before = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        self.log_result(f"-> Baseline Feedback: {fb_before:.0f} RPM")

        if fb_before < 100:
            self.log_result("ERROR: Mock spindle did not spin up. Aborting.")
            return

        # 3. Fault Injection
        self.log_result("\nInjecting encoder fault signal...")
        self.update_progress(50, "Simulating broken cable...")
        self.hal.set_mock_fault('encoder', True)

        # Wait for watchdog timeout (usually 1s + overhead)
        time.sleep(2.0)

        # 4. Analysis
        self.update_progress(70, "Analyzing system response...")

        # Retrieve State
        fb_after = self.hal.get_pin_value(MONITOR_PINS['feedback'])

        # Access mock state safely with defaults
        mock_state: Optional[object] = getattr(self.hal, '_mock_state', None)
        enc_fault = getattr(mock_state, 'encoder_fault', False)
        estop_active = getattr(mock_state, 'estop_triggered', False) or \
            self.hal.get_pin_value('halui.estop.is-activated') is True

        self.log_result(f"\nFeedback post-fault: {fb_after:.0f} RPM")
        self.log_result(f"Encoder Fault Flag:  {'[SET]' if enc_fault else '[CLEAR]'}")
        self.log_result(f"E-Stop State:        {'[TRIPPED]' if estop_active else '[OK]'}")

        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")

        # Verification Logic
        success = True

        if enc_fault:
            self.log_result("  [PASS] Encoder fault flag detected.")
        else:
            self.log_result("  [FAIL] System ignored the injected fault.")
            success = False

        if estop_active or fb_after < (fb_before * 0.1):
            self.log_result("  [PASS] System correctly shut down (E-stop or Spin Down).")
        else:
            self.log_result("  [FAIL] Spindle continued running despite fault.")
            success = False

        if success:
            self.log_result("\nRESULT: Watchdog logic is functional in simulation.")
        else:
            self.log_result("\nRESULT: Watchdog logic FAILED.")

    def _cleanup_system(self) -> None:
        """Force system into a safe state."""
        self.update_progress(90, "Cleaning up...")
        self.log_result("\nResetting simulation state...")

        # Clear mock fault
        self.hal.set_mock_fault('encoder', False)

        # Stop spindle
        self.hal.send_mdi("M5")
        time.sleep(0.5)

        self.update_progress(100, "Test Complete")

    def _show_safety_warning(self) -> None:
        """Show blocking popup for safety."""
        if _HAS_TKINTER and messagebox:
            messagebox.showwarning(
                "Mock Only",
                "This test is restricted to MOCK MODE.\n\n"
                "Testing watchdog on real hardware requires:\n"
                "1. Spindle OFF\n"
                "2. Oscilloscope verification\n"
                "3. Controlled physical disconnection\n\n"
                "Test Aborted."
            )
        else:
            print("!!! SAFETY WARNING: Mock test aborted on real hardware !!!")
