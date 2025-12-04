#!/usr/bin/env python3
"""
Spindle Tuner - Data Logging & Performance Metrics

Handles data buffering, CSV export, and performance metric calculations.

Features:
- Circular buffer for real-time plotting
- Full session recording for export
- Monotonic timing for clock-jump immunity
- CSV export with timestamps
- Performance metrics calculation
"""

import csv
import time
from datetime import datetime
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Deque, Tuple

from config import UPDATE_INTERVAL_MS, HISTORY_DURATION_S


@dataclass
class PerformanceMetrics:
    """Performance metrics from test runs."""
    rise_time_s: float = 0.0       # Time from 10% to 90%
    settling_time_s: float = 0.0   # Time to stay within 2% band
    overshoot_pct: float = 0.0     # Peak overshoot percentage
    steady_state_error: float = 0.0
    max_error: float = 0.0
    load_recovery_time_s: float = 0.0
    thermal_drift_rpm: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DataPoint:
    """Single data point for logging."""
    timestamp: float
    cmd_raw: float
    cmd_limited: float
    feedback: float
    error: float
    errorI: float
    output: float
    at_speed: bool
    
    def to_csv_row(self) -> List:
        return [
            datetime.fromtimestamp(self.timestamp).isoformat(),
            f"{self.timestamp - int(self.timestamp):.3f}",
            f"{self.cmd_raw:.1f}",
            f"{self.cmd_limited:.1f}",
            f"{self.feedback:.1f}",
            f"{self.error:.2f}",
            f"{self.errorI:.2f}",
            f"{self.output:.2f}",
            "1" if self.at_speed else "0",
        ]


class DataLogger:
    """
    Manages data collection, buffering, and export.
    
    Features:
    - Circular buffer for real-time plotting
    - Full session recording for export
    - CSV export with timestamps
    - Performance metrics calculation
    """
    
    def __init__(self, buffer_duration_s: float = HISTORY_DURATION_S):
        """Initialize data logger with specified buffer duration."""
        # Calculate buffer size based on update rate
        self.buffer_size = int(buffer_duration_s * 1000 / UPDATE_INTERVAL_MS)
        
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
    
    def add_sample(self, values: Dict[str, float]):
        """Add a new data sample."""
        now = time.time()
        now_mono = time.monotonic()
        
        if self._start_time_mono is None:
            self._start_time_mono = now_mono
        
        relative_time = now_mono - self._start_time_mono
        
        # Update circular buffers
        self.time_buffer.append(relative_time)
        self.cmd_buffer.append(values.get('cmd_limited', 0))
        self.feedback_buffer.append(values.get('feedback', 0))
        self.error_buffer.append(values.get('error', 0))
        self.errorI_buffer.append(values.get('errorI', 0))
        
        # Record if enabled
        if self.recording:
            point = DataPoint(
                timestamp=now,
                cmd_raw=values.get('cmd_raw', 0),
                cmd_limited=values.get('cmd_limited', 0),
                feedback=values.get('feedback', 0),
                error=values.get('error', 0),
                errorI=values.get('errorI', 0),
                output=values.get('output', 0),
                at_speed=values.get('at_speed', 0) > 0.5,
            )
            self.recorded_data.append(point)
    
    def get_plot_data(self) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
        """Get data for plotting."""
        return (
            list(self.time_buffer),
            list(self.cmd_buffer),
            list(self.feedback_buffer),
            list(self.error_buffer),
            list(self.errorI_buffer),
        )
    
    def clear_buffers(self):
        """Clear all plot buffers."""
        self.time_buffer.clear()
        self.cmd_buffer.clear()
        self.feedback_buffer.clear()
        self.error_buffer.clear()
        self.errorI_buffer.clear()
        self._start_time_mono = None
    
    def clear_recording(self):
        """Clear recorded data."""
        self.recorded_data.clear()
        self.session_start = time.time()
    
    def set_recording(self, enabled: bool):
        """Enable or disable recording."""
        self.recording = enabled
    
    def get_point_count(self) -> int:
        """Get number of recorded points."""
        return len(self.recorded_data)
    
    def export_csv(self, filepath: Path) -> bool:
        """Export recorded data to CSV file."""
        if not self.recorded_data:
            return False
        
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'time_s', 'cmd_raw', 'cmd_limited',
                    'feedback', 'error', 'errorI', 'output', 'at_speed'
                ])
                
                for point in self.recorded_data:
                    writer.writerow(point.to_csv_row())
            
            return True
        except Exception as e:
            print(f"CSV export failed: {e}")
            return False
    
    def calculate_step_metrics(self, start_rpm: float, end_rpm: float,
                               test_data: List[Tuple[float, float]]) -> PerformanceMetrics:
        """
        Calculate performance metrics from step response test data.
        
        Args:
            start_rpm: Starting RPM before step
            end_rpm: Target RPM after step
            test_data: List of (time, rpm) tuples
        
        Returns:
            PerformanceMetrics with calculated values
        """
        if not test_data or len(test_data) < 10:
            return PerformanceMetrics()
        
        metrics = PerformanceMetrics()
        step_size = end_rpm - start_rpm
        
        if abs(step_size) < 10:
            return metrics
        
        # Find step start (when command changes)
        step_start_time = test_data[0][0]
        
        # Calculate thresholds
        rpm_10 = start_rpm + 0.1 * step_size
        rpm_90 = start_rpm + 0.9 * step_size
        rpm_98 = start_rpm + 0.98 * step_size
        rpm_102 = start_rpm + 1.02 * step_size
        
        # Find rise time (10% to 90%)
        time_10 = None
        time_90 = None
        
        for t, rpm in test_data:
            if time_10 is None and rpm >= rpm_10:
                time_10 = t
            if time_90 is None and rpm >= rpm_90:
                time_90 = t
                break
        
        if time_10 is not None and time_90 is not None:
            metrics.rise_time_s = time_90 - time_10
        
        # Find settling time (within 2% band)
        settling_time = None
        in_band_since = None
        
        for t, rpm in test_data:
            in_band = rpm_98 <= rpm <= rpm_102
            if in_band:
                if in_band_since is None:
                    in_band_since = t
            else:
                in_band_since = None
            
            # Require 0.5s in band to count as settled
            if in_band_since is not None and (t - in_band_since) >= 0.5:
                settling_time = in_band_since - step_start_time
                break
        
        if settling_time is not None:
            metrics.settling_time_s = settling_time
        
        # Calculate overshoot
        peak_rpm = max(rpm for _, rpm in test_data)
        if step_size > 0:
            overshoot = peak_rpm - end_rpm
            if overshoot > 0:
                metrics.overshoot_pct = (overshoot / step_size) * 100
        
        # Calculate max error
        errors = [abs(rpm - end_rpm) for _, rpm in test_data[-50:]]  # Last ~5 seconds
        if errors:
            metrics.max_error = max(errors)
            metrics.steady_state_error = sum(errors) / len(errors)
        
        return metrics
    
    def calculate_load_metrics(self, test_data: List[Tuple[float, float]],
                               target_rpm: float) -> PerformanceMetrics:
        """
        Calculate metrics from load recovery test.
        
        Args:
            test_data: List of (time, rpm) tuples during load test
            target_rpm: Target RPM during test
        
        Returns:
            PerformanceMetrics with load recovery data
        """
        if not test_data:
            return PerformanceMetrics()
        
        metrics = PerformanceMetrics()
        
        # Find minimum RPM (maximum droop)
        min_rpm = min(rpm for _, rpm in test_data)
        droop = target_rpm - min_rpm
        
        if droop > 5:  # Significant load was applied
            # Find when droop reached minimum
            min_time = None
            for t, rpm in test_data:
                if rpm == min_rpm:
                    min_time = t
                    break
            
            # Find recovery time (back within 20 RPM)
            if min_time is not None:
                recovery_threshold = target_rpm - 20
                for t, rpm in test_data:
                    if t > min_time and rpm >= recovery_threshold:
                        metrics.load_recovery_time_s = t - min_time
                        break
        
        return metrics
