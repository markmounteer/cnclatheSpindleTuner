"""
Full Test Suite

Runs an abbreviated sequence of all major tests.
"""

import time

try:
    from tkinter import messagebox
    _HAS_TKINTER = True
except ImportError:
    messagebox = None
    _HAS_TKINTER = False

from tests.base import BaseTest, TestDescription


class FullSuiteTest(BaseTest):
    """Full test suite runner."""

    TEST_NAME = "Full Test Suite"
    GUIDE_REF = ""

    def __init__(self, *args, test_instances: dict = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_instances = test_instances or {}

    def set_test_instances(self, instances: dict):
        """Set the test instances to run."""
        self.test_instances = instances

    @classmethod
    def get_description(cls) -> TestDescription:
        return TestDescription(
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

        if not messagebox.askyesno(
            "Full Test Suite",
            "This will run a sequence of tests:\n\n"
            "1. Signal Chain Check\n"
            "2. Open Loop Test\n"
            "3. Forward PID Test\n"
            "4. Step Response\n\n"
            "Total time: ~2 minutes\n\n"
            "Continue?"):
            self.end_test()
            return

        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute full test suite."""
        self.log_header()

        tests = [
            ("Signal Chain", "signal_chain"),
            ("Open Loop", "open_loop"),
            ("Forward PID", "forward"),
            ("Step Response", "step"),
        ]

        total = len(tests)
        passed = 0
        failed = 0

        for i, (name, key) in enumerate(tests):
            if self.test_abort:
                self.log_result(f"\n>>> Suite aborted at {name}")
                break

            progress = (i / total) * 90
            self.update_progress(progress, f"Running {name}...")
            self.log_result(f"\n>>> Running {name} <<<")

            test_instance = self.test_instances.get(key)
            if test_instance:
                # Run the test's internal sequence directly
                test_instance.test_running = True
                test_instance.test_abort = False
                try:
                    test_instance._sequence()
                    passed += 1
                except Exception as e:
                    self.log_result(f"  ERROR: {e}")
                    failed += 1
                test_instance.test_running = False
            else:
                self.log_result(f"  Test not available: {key}")
                failed += 1

            time.sleep(1.0)

        self.update_progress(100, "Suite complete")

        self.log_result(f"\n{'='*50}")
        self.log_result("FULL SUITE SUMMARY")
        self.log_result("="*50)
        self.log_result(f"  Tests run: {passed + failed}")
        self.log_result(f"  Passed: {passed}")
        self.log_result(f"  Failed/Skipped: {failed}")

        if failed == 0 and not self.test_abort:
            self.log_footer("ALL TESTS PASSED")
        elif self.test_abort:
            self.log_footer("ABORTED")
        else:
            self.log_footer(f"{failed} ISSUES")

        self.end_test()
