"""
Full Test Suite

Runs an abbreviated sequence of all major tests.
"""

import time
from typing import Dict, Optional, List, Tuple

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None  # type: ignore[assignment]
    _HAS_TKINTER = False

from tests.base import BaseTest, ProcedureDescription


class FullSuiteTest(BaseTest):
    """Full test suite runner."""

    TEST_NAME = "Full Test Suite"
    GUIDE_REF = ""

    def __init__(self, *args, test_instances: Optional[Dict[str, BaseTest]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_instances = test_instances or {}

    def set_test_instances(self, instances: Dict[str, BaseTest]):
        """Set the test instances to run."""
        self.test_instances = instances

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Full Test Suite",
            guide_ref="",
            purpose="""
Run an abbreviated sequence of all major tests in order:

1. Signal Chain Check (§5.1)
2. Open Loop Test (§6.1)
3. Forward PID Test (§6.2)
4. Step Response Test (§7.1)

This provides a quick comprehensive assessment of the
tuning configuration in about 2 minutes.""",

            prerequisites=[
                "Machine powered on and ready",
                "E-stop tested and functional",
                "Clear area around spindle",
                "Allow 2-3 minutes for full suite",
            ],

            procedure=[
                "1. Click 'Run All Tests' to begin",
                "2. Confirm the test sequence",
                "3. Tests run automatically in sequence",
                "4. Results logged for each test",
                "5. Summary provided at end",
            ],

            expected_results=[
                "All individual tests should pass",
                "Review any warnings from individual tests",
                "Total time ~2 minutes",
            ],

            troubleshooting=[
                "If any test fails:",
                "  -> Run that specific test individually",
                "  -> Review its troubleshooting section",
                "  -> Fix issue before continuing suite",
                "Suite can be aborted at any time",
            ],

            safety_notes=[
                "Multiple tests run in sequence",
                "Spindle starts and stops multiple times",
                "Keep hand near E-stop throughout",
                "Abort stops current test immediately",
            ]
        )

    def run(self):
        """Start full suite with confirmation."""
        if not self.start_test():
            return

        # UI Confirmation (Only if GUI is available)
        if _HAS_TKINTER and messagebox:
            if not messagebox.askyesno(
                "Full Test Suite",
                "This will run a sequence of tests:\n\n"
                "1. Signal Chain Check\n"
                "2. Open Loop Test\n"
                "3. Forward PID Test\n"
                "4. Step Response\n\n"
                "Total time: ~2 minutes\n\n"
                "Continue?"
            ):
                self.end_test()
                return

        # If no GUI, we assume automated run and proceed
        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute full test suite."""
        self.log_header()
        self.log_result("Starting Full Diagnostic Suite...")

        tests: List[Tuple[str, str]] = [
            ("Signal Chain", "signal_chain"),
            ("Open Loop", "open_loop"),
            ("Forward PID", "forward"),
            ("Step Response", "step"),
        ]

        total = len(tests)
        passed = 0
        failed = 0
        skipped = 0

        for i, (name, key) in enumerate(tests):
            # 1. Check for Abort Request
            if self.test_abort:
                self.log_result(f"\n>>> Suite aborted by user before {name}")
                skipped = total - i
                break

            # 2. Update Progress
            progress = (i / total) * 90
            self.update_progress(progress, f"Running {name}...")

            # Visual separator for logs
            self.log_result(f"\n{'-'*40}")
            self.log_result(f"TEST {i+1}/{total}: {name}")
            self.log_result(f"{'-'*40}")

            # 3. Retrieve Test Instance
            test_instance = self.test_instances.get(key)

            if not test_instance:
                self.log_result(f"  ERROR: Test module '{key}' not found/initialized.")
                failed += 1
                continue

            # 4. Execute Sub-Test
            # We manually set state to simulate the test running without triggering
            # its individual UI start/stop events (popups).
            test_instance.test_running = True
            test_instance.test_abort = False  # Reset abort state for the specific test

            try:
                # Run the internal sequence of the sub-test
                test_instance._sequence()
                passed += 1
                self.log_result(f"  > {name}: COMPLETED")
            except Exception as e:
                self.log_result(f"  > {name}: FAILED with error: {str(e)}")
                failed += 1
            finally:
                # Crucial: Ensure the sub-test flag is reset even if it crashes
                test_instance.test_running = False

            # Propagate abort signal to sub-test if user requested abort
            if self.test_abort:
                test_instance.test_abort = True

            # Small pause between tests for machine settling
            time.sleep(1.0)

        # 5. Final Summary
        self.update_progress(100, "Suite complete")

        self.log_result(f"\n{'='*50}")
        self.log_result("FULL SUITE SUMMARY")
        self.log_result("=" * 50)
        self.log_result(f"  Total Tests:  {total}")
        self.log_result(f"  Passed:       {passed}")
        self.log_result(f"  Failed:       {failed}")
        if skipped > 0:
            self.log_result(f"  Skipped:      {skipped}")

        if self.test_abort:
            self.log_footer("SUITE ABORTED")
        elif failed == 0:
            self.log_footer("ALL TESTS PASSED")
        else:
            self.log_footer(f"COMPLETED WITH {failed} ERRORS")

        self.end_test()
