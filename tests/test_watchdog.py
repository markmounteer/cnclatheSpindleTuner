"""
Mock Watchdog Test (Guide §6.6)

Safe encoder watchdog simulation - MOCK MODE ONLY.
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


class WatchdogTest(BaseTest):
    """Mock encoder watchdog test (Guide §6.6)."""

    TEST_NAME = "Encoder Watchdog Test"
    GUIDE_REF = "Guide §6.6"

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
            name="Encoder Watchdog Test (Mock)",
            guide_ref="§6.6",
            purpose="""
Safely test the encoder watchdog behavior using programmatic
fault injection in MOCK MODE ONLY.

On real hardware, the encoder watchdog should trigger an E-stop
within ~1 second if the encoder signal is lost while the spindle
is running. This prevents dangerous runaway conditions.

This test safely simulates that behavior without requiring
physical cable disconnection.""",

            prerequisites=[
                "Running in MOCK MODE",
                "Real hardware testing should be done during",
                "  initial commissioning with spindle stopped",
            ],

            procedure=[
                "1. Click 'Run Test' (mock mode only)",
                "2. Mock spindle starts at 1000 RPM",
                "3. Encoder fault injected programmatically",
                "4. System response observed",
                "5. Fault cleared and spindle stopped",
            ],

            expected_results=[
                "Encoder fault flag becomes SET",
                "Mock system responds to fault condition",
                "On real hardware, this would trigger:",
                "  - Watchdog timeout",
                "  - External-OK signal drop",
                "  - E-stop via safety chain",
            ],

            troubleshooting=[
                "Test only runs in mock mode:",
                "  -> Start application with --mock flag",
                "For real hardware testing:",
                "  -> Verify during initial commissioning",
                "  -> Test with spindle STOPPED",
                "  -> Use oscilloscope to verify timing",
            ],

            safety_notes=[
                ">>> MOCK MODE ONLY <<<",
                "Real watchdog testing requires different procedure",
                "Never disconnect encoder while spindle running",
                "Real test should verify <1 second response time",
            ]
        )

    def run(self):
        """Start mock watchdog test."""
        if not self.hal.is_mock:
            messagebox.showinfo(
                "Mock Only",
                "This test only runs in mock mode for safety.\n\n"
                "On real hardware, encoder watchdog behavior should be\n"
                "verified during initial commissioning with the spindle\n"
                "stopped and proper safety procedures in place.")
            return

        if not self.start_test():
            return

        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute safe mock watchdog test."""
        self.log_header()
        self.log_result("This is a SAFE simulation - no physical disconnection required.")
        self.update_progress(0, "Starting mock spindle...")

        # Start spindle in mock mode
        self.hal.send_mdi("M3 S1000")
        self.log_result("\nStarting spindle at 1000 RPM...")
        time.sleep(2)

        self.update_progress(20, "Reading baseline...")

        fb_before = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        self.log_result(f"Feedback before fault: {fb_before:.0f} RPM")

        # Inject encoder fault programmatically
        self.log_result("\nInjecting encoder fault via set_mock_fault()...")
        self.update_progress(40, "Injecting fault...")

        self.hal.set_mock_fault('encoder', True)
        time.sleep(1.5)

        self.update_progress(60, "Checking response...")

        # Check response
        fb_after = self.hal.get_pin_value(MONITOR_PINS['feedback'])
        enc_fault = getattr(self.hal._mock_state, 'encoder_fault', False)
        estop = getattr(self.hal._mock_state, 'estop_triggered', False)

        self.log_result(f"\nFeedback after fault: {fb_after:.0f} RPM")
        self.log_result(f"Encoder fault flag: {'SET' if enc_fault else 'CLEAR'}")
        self.log_result(f"E-stop triggered: {'YES' if estop else 'NO'}")

        # Analysis
        self.log_result(f"\n{'='*50}")
        self.log_result("ANALYSIS:")

        if enc_fault:
            self.log_result("  [OK] Encoder fault was detected")
        else:
            self.log_result("  [FAIL] Encoder fault not detected")

        if fb_after < fb_before * 0.5 or estop:
            self.log_result("  [OK] Mock system responded to fault")
            self.log_result("\nIn a real system, this would trigger:")
            self.log_result("  - Watchdog timeout (encoder.00.watchdog)")
            self.log_result("  - External-OK signal drop")
            self.log_result("  - E-stop via safety chain")
        else:
            self.log_result("  [INFO] Mock system continued running")
            self.log_result("    (This tests the mock, not real watchdog)")

        # Clear fault and stop
        self.log_result("\nClearing fault and stopping...")
        self.update_progress(80, "Clearing fault...")

        self.hal.set_mock_fault('encoder', False)
        self.hal.send_mdi("M5")

        self.update_progress(100, "Complete")

        self.log_footer("MOCK TEST COMPLETE")
        self.log_result("\nNote: Real watchdog testing should be done during")
        self.log_result("commissioning with spindle OFF and oscilloscope/")
        self.log_result("logic analyzer to verify timing.")

        self.end_test()
