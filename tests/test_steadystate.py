"""
Steady-State Test (Guide §7.3)

Monitors steady-state accuracy and thermal drift over time.
"""

import csv
import os
import time
from datetime import datetime
from typing import Optional

from config import MONITOR_PINS
from tests.base import BaseTest, ProcedureDescription, TARGETS


class SteadyStateTest(BaseTest):
    """
    Steady-state accuracy test (Guide §7.3).
    Monitors speed stability, steady-state error, and thermal drift.
    """

    TEST_NAME = "Steady-State Test"
    GUIDE_REF = "Guide §7.3"

    def __init__(self, *args, duration: int = 30, target_rpm: float = 1000.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.duration = duration
        self.target_rpm = target_rpm

    def set_duration(self, duration: int):
        """Set the monitoring duration in seconds (10s to 10 mins)."""
        self.duration = max(10, min(600, duration))

    def set_rpm(self, rpm: float):
        """Set the target RPM for the test."""
        self.target_rpm = max(100, min(3000, rpm))

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Steady-State Accuracy Test",
            guide_ref="§7.3",
            purpose="""
Monitor spindle speed stability over an extended period.
Measures:
- Steady-State Error: Difference between Target and Average RPM.
- Speed Variation (Noise): Standard deviation and Peak-to-Peak.
- Thermal Drift: Change in Integrator (I-term) load over time.

Longer durations (120s+) are required to characterize thermal drift.""",
            prerequisites=[
                "Step and load tests completed",
                "Spindle warmed up (unless testing cold-start drift)",
            ],
            procedure=[
                "1. Set Duration (default 30s) and Target RPM.",
                "2. System accelerates to Target RPM.",
                "3. Wait 4 seconds for stabilization.",
                "4. Sample Feedback, Error, and Integrator at 20Hz.",
                "5. Calculate statistics and save CSV log.",
            ],
            expected_results=[
                "Steady-state error: < 1% of Target RPM",
                "Peak-to-peak noise: < 2% of Target RPM",
                "Integrator Drift: Steady increase/decrease (Thermal comp)",
                "No rhythmic oscillation (Hunting)",
            ],
            troubleshooting=[
                "High 'Hunting' Variation:",
                "  -> Reduce P-gain (overshoot) or I-gain (windup)",
                "  -> Check encoder coupling/belt tension",
                "Large Steady-State Error:",
                "  -> Increase I-gain",
                "  -> Ensure 'maxerrorI' is not capping the integrator",
                "No Integrator Drift (during long run):",
                "  -> I-gain too low to compensate for heat",
            ],
            safety_notes=[
                "Spindle will run continuously.",
                "Ensure chuck key is removed.",
                "Monitor motor temperature manually during long tests.",
            ]
        )

    def run(self, duration: Optional[int] = None, rpm: Optional[float] = None):
        """Start steady-state test with optional duration and RPM overrides."""
        if duration is not None:
            self.set_duration(duration)
        if rpm is not None:
            self.set_rpm(rpm)

        if not self.start_test():
            return

        self.run_sequence(self._sequence)

    def _sequence(self):
        """Execute steady-state monitoring sequence."""
        self.log_header(f"STEADY-STATE TEST ({self.duration}s @ {self.target_rpm} RPM)")

        # 1. Spin up
        self.update_progress(0, f"Spinning up to {self.target_rpm} RPM...")
        self.hal.send_mdi(f"M3 S{self.target_rpm}")
        time.sleep(4)  # Allow initial settling

        # Check for immediate abort
        if self.test_abort:
            self.hal.send_mdi("M5")
            self.end_test()
            return

        # 2. Monitoring Loop
        self.log_result(f"Acquiring data at 20Hz for {self.duration} seconds...")

        data_points = []
        start_time = time.time()

        # 20Hz sampling = 0.05s period
        sample_period = 0.05

        while (time.time() - start_time) < self.duration:
            if self.test_abort:
                break

            loop_start = time.time()
            elapsed = loop_start - start_time

            # Capture synchronized data
            sample = {
                'time': elapsed,
                'rpm': self.hal.get_pin_value(MONITOR_PINS['feedback']),
                'error': self.hal.get_pin_value(MONITOR_PINS['error']),
                'integrator': self.hal.get_pin_value(MONITOR_PINS['errorI'])
            }
            data_points.append(sample)

            # Update UI every ~500ms (every 10th sample) to reduce overhead
            if len(data_points) % 10 == 0:
                progress = 5 + (elapsed / self.duration) * 85
                self.update_progress(progress, f"Monitoring... {elapsed:.1f}s")

            # Precise timing sleep
            computation_time = time.time() - loop_start
            sleep_time = sample_period - computation_time
            if sleep_time > 0:
                time.sleep(sleep_time)

        # 3. Shutdown
        self.hal.send_mdi("M5")
        self.update_progress(95, "Calculating statistics...")

        if not data_points or self.test_abort:
            self.log_result("  Test aborted or no data collected.")
            self.end_test()
            return

        # 4. Analysis
        rpms = [d['rpm'] for d in data_points]
        integrators = [d['integrator'] for d in data_points]

        stats = self.calculate_statistics(rpms)

        # Drift calculations
        total_drift_i = integrators[-1] - integrators[0]
        drift_rate_minute = total_drift_i * (60.0 / self.duration)

        ss_error = self.target_rpm - stats['avg']

        # 5. Reporting
        self.log_result(f"\nRESULTS (@ {self.target_rpm} RPM):")
        self.log_result(f"  Avg RPM:       {stats['avg']:.2f}")
        self.log_result(f"  SS Error:      {ss_error:.2f} RPM (Target: {self.target_rpm})")
        self.log_result(f"  Noise (Pk-Pk): {stats['range']:.2f} RPM")
        self.log_result(f"  Std Dev:       {stats['std_dev']:.3f}")
        self.log_result(f"  Integrator:    {integrators[0]:.1f} -> {integrators[-1]:.1f} (Delta: {total_drift_i:+.2f})")
        self.log_result(f"  Drift Rate:    {drift_rate_minute:+.2f} per min")

        self.evaluate_performance(stats['range'], ss_error, total_drift_i)

        # 6. Save Data
        self.save_csv_data(data_points)

        self.end_test()

    def evaluate_performance(self, noise_pk_pk, ss_error, drift):
        """Compare results against targets and print assessment."""
        self.log_result("\nASSESSMENT (Guide §7.4):")

        # Steady State Error Assessment
        abs_err = abs(ss_error)
        if abs_err < TARGETS.ss_error_excellent:
            grade_err = "EXCELLENT"
        elif abs_err < TARGETS.ss_error_good:
            grade_err = "GOOD"
        else:
            grade_err = "FAIL - Increase I-gain"
        self.log_result(f"  Accuracy: {grade_err}")

        # Noise Assessment
        if noise_pk_pk < TARGETS.noise_excellent:
            grade_noise = "EXCELLENT"
        elif noise_pk_pk < TARGETS.noise_good:
            grade_noise = "GOOD"
        else:
            grade_noise = "HIGH VARIANCE - Check P-gain or mechanicals"
        self.log_result(f"  Stability: {grade_noise}")

        # Thermal Assessment
        if self.duration > 59 and abs(drift) > 5.0:
            self.log_result("  Thermal: I-term is actively compensating for heat (Normal behavior).")
        elif self.duration > 59 and abs(drift) < 1.0:
            self.log_result("  Thermal: Little to no drift detected (Check if I-gain is too low?)")

        # Footer Grade
        if "EXCELLENT" in grade_err and "EXCELLENT" in grade_noise:
            self.log_footer("EXCELLENT")
        elif "FAIL" in grade_err or "HIGH VARIANCE" in grade_noise:
            self.log_footer("NEEDS TUNING")
        else:
            self.log_footer("GOOD")

    def save_csv_data(self, data):
        """Save time-series data to CSV for external plotting."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"steady_state_{int(self.target_rpm)}rpm_{timestamp}.csv"

        try:
            # Create logs directory if it doesn't exist
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            filepath = os.path.join(log_dir, filename)

            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['time', 'rpm', 'error', 'integrator'])
                writer.writeheader()
                writer.writerows(data)

            self.log_result(f"\n  [Data saved to {filepath}]")
        except Exception as e:
            self.log_result(f"\n  [Error saving CSV: {e}]")
