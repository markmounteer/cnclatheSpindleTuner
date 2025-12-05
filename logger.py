#!/usr/bin/env python3
"""
Spindle Tuner - Data Logging & Performance Metrics

Handles data buffering, CSV export, and performance metric calculations.
"""

from __future__ import annotations

import csv
import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from config import UPDATE_INTERVAL_MS, HISTORY_DURATION_S

log = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics from test runs."""

    rise_time_s: float = 0.0  # Time from 10% to 90%
    settling_time_s: float = 0.0  # Time after which signal stays within 2% band
    overshoot_pct: float = 0.0  # Peak overshoot percentage
    steady_state_error: float = 0.0  # Average error in steady state (signed)
    max_error: float = 0.0  # Maximum absolute error during test
    load_recovery_time_s: float = 0.0  # Time to recover from load step
    thermal_drift_rpm: float = 0.0  # RPM drift over time (steady-state test)
    iae: float = 0.0  # Integral of Absolute Error

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class DataPoint:
    """Single data point for logging."""

    timestamp: float  # Epoch time
    relative_time: float  # Monotonic time from start of session
    cmd_raw: float
    cmd_limited: float
    feedback: float
    error: float
    errorI: float
    output: float
    at_speed: bool

    def to_csv_row(self) -> List[str]:
        return [
            datetime.fromtimestamp(self.timestamp).isoformat(),
            f"{self.relative_time:.4f}",
            f"{self.cmd_raw:.2f}",
            f"{self.cmd_limited:.2f}",
            f"{self.feedback:.2f}",
            f"{self.error:.3f}",
            f"{self.errorI:.3f}",
            f"{self.output:.2f}",
            "1" if self.at_speed else "0",
        ]


class DataLogger:
    """
    Manages data collection, buffering, and export.

    - Thread-safe circular buffer for real-time plotting
    - Full session recording for export
    - Monotonic clock for accurate relative timing
    - Step/load performance metrics (rise/settling/overshoot/IAE)
    """

    def __init__(self, buffer_duration_s: float = HISTORY_DURATION_S):
        self._lock = threading.RLock()

        # Guard against misconfig: always keep >= 1 sample of history.
        self.buffer_size = max(1, int(buffer_duration_s * 1000 / UPDATE_INTERVAL_MS))

        # Circular buffers for plotting (time-limited)
        self.time_buffer: Deque[float] = deque(maxlen=self.buffer_size)
        self.cmd_buffer: Deque[float] = deque(maxlen=self.buffer_size)
        self.feedback_buffer: Deque[float] = deque(maxlen=self.buffer_size)
        self.error_buffer: Deque[float] = deque(maxlen=self.buffer_size)
        self.errorI_buffer: Deque[float] = deque(maxlen=self.buffer_size)

        # Full session recording (unlimited, for export)
        self.recording: bool = True
        self.recorded_data: List[DataPoint] = []

        # Session tracking
        self.session_start: float = time.time()
        self._start_time_mono: Optional[float] = None

    # ---------------------------------------------------------------------
    # Data ingestion / retrieval
    # ---------------------------------------------------------------------

    def add_sample(self, values: Dict[str, float]) -> None:
        """Add a new data sample in a thread-safe manner."""
        now_epoch = time.time()
        now_mono = time.monotonic()

        with self._lock:
            if self._start_time_mono is None:
                self._start_time_mono = now_mono

            relative_time = now_mono - self._start_time_mono

            cmd_limited = float(values.get("cmd_limited", 0.0))
            feedback = float(values.get("feedback", 0.0))
            error = float(values.get("error", 0.0))
            errorI = float(values.get("errorI", 0.0))

            self.time_buffer.append(relative_time)
            self.cmd_buffer.append(cmd_limited)
            self.feedback_buffer.append(feedback)
            self.error_buffer.append(error)
            self.errorI_buffer.append(errorI)

            if not self.recording:
                return

            self.recorded_data.append(
                DataPoint(
                    timestamp=now_epoch,
                    relative_time=relative_time,
                    cmd_raw=float(values.get("cmd_raw", 0.0)),
                    cmd_limited=cmd_limited,
                    feedback=feedback,
                    error=error,
                    errorI=errorI,
                    output=float(values.get("output", 0.0)),
                    at_speed=values.get("at_speed", 0.0) > 0.5,
                )
            )

    def get_plot_data(self) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
        """Get a copy of time-series buffers for plotting (thread-safe)."""
        with self._lock:
            return (
                list(self.time_buffer),
                list(self.cmd_buffer),
                list(self.feedback_buffer),
                list(self.error_buffer),
                list(self.errorI_buffer),
            )

    def clear_buffers(self) -> None:
        """Clear all plot buffers (and reset the relative timer)."""
        with self._lock:
            self.time_buffer.clear()
            self.cmd_buffer.clear()
            self.feedback_buffer.clear()
            self.error_buffer.clear()
            self.errorI_buffer.clear()
            self._start_time_mono = None

    def clear_recording(self) -> None:
        """Clear recorded data (export history)."""
        with self._lock:
            self.recorded_data.clear()
            self.session_start = time.time()

    def set_recording(self, enabled: bool) -> None:
        """Enable or disable data recording."""
        self.recording = bool(enabled)

    def get_point_count(self) -> int:
        """Get number of recorded points."""
        with self._lock:
            return len(self.recorded_data)

    # ---------------------------------------------------------------------
    # CSV export
    # ---------------------------------------------------------------------

    def export_csv(self, filepath: Path, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Export recorded data to a CSV file."""
        with self._lock:
            if not self.recorded_data:
                return False
            data_copy = list(self.recorded_data)

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with filepath.open("w", newline="") as f:
                writer = csv.writer(f)

                if metadata:
                    writer.writerow(["# Metadata"])
                    for k, v in metadata.items():
                        writer.writerow([f"# {k}", v])
                    writer.writerow([])  # spacer

                writer.writerow(
                    [
                        "timestamp_iso",
                        "time_s",
                        "cmd_raw",
                        "cmd_limited",
                        "feedback",
                        "error",
                        "errorI",
                        "output",
                        "at_speed",
                    ]
                )

                for point in data_copy:
                    writer.writerow(point.to_csv_row())

            return True
        except Exception:
            log.exception("CSV export failed for %s", filepath)
            return False

    # ---------------------------------------------------------------------
    # Metrics helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _interpolate_time(t1: float, y1: float, t2: float, y2: float, target_y: float) -> float:
        """Linear interpolation to find time t where y == target_y."""
        if y2 == y1:
            return t1
        frac = (target_y - y1) / (y2 - y1)
        return t1 + frac * (t2 - t1)

    # ---------------------------------------------------------------------
    # Performance metrics
    # ---------------------------------------------------------------------

    def calculate_step_metrics(
        self,
        start_rpm: float,
        end_rpm: float,
        test_data: List[Dict[str, float]],
    ) -> PerformanceMetrics:
        """
        Compute step response metrics.

        test_data entries must include:
            'time' (seconds), 'feedback' (rpm), 'error' (rpm)

        Sentinel values:
            rise_time_s / settling_time_s = -1.0 if not determinable.
        """
        if not test_data or len(test_data) < 10:
            return PerformanceMetrics()

        metrics = PerformanceMetrics()
        step_size = end_rpm - start_rpm
        if abs(step_size) < 10:
            return metrics

        # Ensure monotonic ordering (robust against duplicates / slight disorder).
        data = sorted(test_data, key=lambda p: p.get("time", 0.0))
        step_start_time = float(data[0].get("time", 0.0))

        rpm_10 = start_rpm + 0.1 * step_size
        rpm_90 = start_rpm + 0.9 * step_size

        # 2% settling band relative to the step size
        band = 0.02 * abs(step_size)
        lower_band, upper_band = end_rpm - band, end_rpm + band

        time_10: Optional[float] = None
        time_90: Optional[float] = None

        peak_rpm = -float("inf") if step_size > 0 else float("inf")
        prev_t: Optional[float] = None
        prev_rpm: Optional[float] = None
        prev_abs_error: Optional[float] = None

        for point in data:
            t = float(point.get("time", 0.0))
            rpm = float(point.get("feedback", 0.0))
            abs_error = abs(float(point.get("error", 0.0)))

            # Peak detection
            if step_size > 0:
                if rpm > peak_rpm:
                    peak_rpm = rpm
            else:
                if rpm < peak_rpm:
                    peak_rpm = rpm

            # IAE: trapezoidal integration; ignore non-increasing dt
            if prev_t is not None and prev_abs_error is not None:
                dt = t - prev_t
                if dt > 0:
                    metrics.iae += 0.5 * (prev_abs_error + abs_error) * dt

            # Rise time interpolation
            if prev_t is not None and prev_rpm is not None:
                if time_10 is None:
                    crossed_10 = (
                        (step_size > 0 and prev_rpm <= rpm_10 <= rpm)
                        or (step_size < 0 and prev_rpm >= rpm_10 >= rpm)
                    )
                    if crossed_10:
                        time_10 = self._interpolate_time(prev_t, prev_rpm, t, rpm, rpm_10)

                if time_90 is None:
                    crossed_90 = (
                        (step_size > 0 and prev_rpm <= rpm_90 <= rpm)
                        or (step_size < 0 and prev_rpm >= rpm_90 >= rpm)
                    )
                    if crossed_90:
                        time_90 = self._interpolate_time(prev_t, prev_rpm, t, rpm, rpm_90)

            prev_t, prev_rpm, prev_abs_error = t, rpm, abs_error

        metrics.rise_time_s = (
            abs(time_90 - time_10) if (time_10 is not None and time_90 is not None) else -1.0
        )

        # Overshoot (% of step magnitude)
        if step_size > 0:
            overshoot = peak_rpm - end_rpm
            metrics.overshoot_pct = (overshoot / step_size * 100.0) if overshoot > 0 else 0.0
        else:
            overshoot = end_rpm - peak_rpm
            metrics.overshoot_pct = (overshoot / abs(step_size) * 100.0) if overshoot > 0 else 0.0

        # Settling time: time after which signal stays within the band
        final_rpm = float(data[-1].get("feedback", 0.0))
        if lower_band <= final_rpm <= upper_band:
            settle_time: Optional[float] = None

            # Find last out-of-band index; settle_time is the *next* sample’s time.
            for i in range(len(data) - 1, -1, -1):
                rpm = float(data[i].get("feedback", 0.0))
                if not (lower_band <= rpm <= upper_band):
                    settle_time = float(data[min(i + 1, len(data) - 1)].get("time", step_start_time))
                    break

            if settle_time is None:
                # Never left the band at all
                settle_time = step_start_time

            metrics.settling_time_s = max(0.0, settle_time - step_start_time)
        else:
            metrics.settling_time_s = -1.0

        # Max error always computable
        metrics.max_error = max(abs(float(p.get("error", 0.0))) for p in data)

        # Steady-state error: average over last 1.0 second (bounded by step start)
        end_time = float(data[-1].get("time", 0.0))
        ss_start = max(step_start_time, end_time - 1.0)
        ss_points = [p for p in data if float(p.get("time", 0.0)) >= ss_start]
        if ss_points:
            avg_rpm = sum(float(p.get("feedback", 0.0)) for p in ss_points) / len(ss_points)
            metrics.steady_state_error = end_rpm - avg_rpm

        return metrics

    def calculate_load_metrics(
        self,
        test_data: List[Tuple[float, float]],
        target_rpm: float,
    ) -> PerformanceMetrics:
        """
        Calculate metrics from a load recovery test.

        Args:
            test_data: List of (time_s, rpm) tuples.
            target_rpm: Target RPM during the test.
        """
        if not test_data:
            return PerformanceMetrics()

        metrics = PerformanceMetrics()

        # Single-pass min search (time, rpm)
        min_idx, (min_time, min_rpm) = min(enumerate(test_data), key=lambda x: x[1][1])
        droop = abs(target_rpm - float(min_rpm))
        if droop <= 5.0:
            return metrics

        recovery_band = 20.0
        for t, rpm in test_data[min_idx:]:
            if abs(float(rpm) - target_rpm) <= recovery_band:
                metrics.load_recovery_time_s = float(t) - float(min_time)
                break
        else:
            metrics.load_recovery_time_s = -1.0

        return metrics

