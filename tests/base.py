"""
Spindle Tuner - Base Test Class

Contains common functionality for all test modules:
- Performance targets from Guide §7.4
- Signal sampling utilities
- Assessment methods
- Test lifecycle management
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from logger import DataLogger


# =============================================================================
# PERFORMANCE TARGETS (Guide §7.4)
# =============================================================================

@dataclass
class PerformanceTargets:
    """Performance targets from Guide §7.4."""
    # Settling time targets
    settling_excellent: float = 2.0  # seconds
    settling_good: float = 3.0

    # Overshoot targets
    overshoot_excellent: float = 5.0  # percent
    overshoot_good: float = 10.0

    # Steady-state error targets
    ss_error_excellent: float = 8.0  # RPM
    ss_error_good: float = 15.0

    # Load recovery targets
    recovery_excellent: float = 2.0  # seconds
    recovery_good: float = 3.0

    # Noise targets
    noise_excellent: float = 10.0  # RPM peak-to-peak
    noise_good: float = 20.0


TARGETS = PerformanceTargets()


# =============================================================================
# TEST DESCRIPTIONS - Detailed info for each test
# =============================================================================

@dataclass
class TestDescription:
    """Description and instructions for a test."""
    name: str
    guide_ref: str
    purpose: str
    prerequisites: List[str]
    procedure: List[str]
    expected_results: List[str]
    troubleshooting: List[str]
    safety_notes: List[str]


# =============================================================================
# BASE TEST CLASS
# =============================================================================

class BaseTest(ABC):
    """
    Abstract base class for all spindle tests.

    Provides common functionality:
    - Signal sampling
    - Performance assessment
    - Test lifecycle management
    - Result logging
    """

    # Class attributes to be overridden by subclasses
    TEST_NAME: str = "Base Test"
    GUIDE_REF: str = ""

    def __init__(self, hal_interface, data_logger,
                 log_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable] = None):
        """
        Initialize base test.

        Args:
            hal_interface: HAL interface for hardware communication
            data_logger: Data logger for recording samples
            log_callback: Optional callback for logging results to UI
            progress_callback: Optional callback for progress updates
        """
        self.hal = hal_interface
        self.logger = data_logger
        self.log_callback = log_callback
        self.progress_callback = progress_callback

        self.test_running = False
        self.test_abort = False

    # =========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =========================================================================

    @classmethod
    @abstractmethod
    def get_description(cls) -> TestDescription:
        """Return detailed description of the test."""
        pass

    @abstractmethod
    def run(self):
        """Execute the test sequence."""
        pass

    # =========================================================================
    # LOGGING UTILITIES
    # =========================================================================

    def log_result(self, text: str):
        """Log text to results area."""
        if self.log_callback:
            self.log_callback(text)

    def update_progress(self, percent: float, message: str = ""):
        """Update progress indicator."""
        if self.progress_callback:
            self.progress_callback(percent, message)

    def log_header(self, title: str = None):
        """Log a test header."""
        name = title or self.TEST_NAME
        ref = f" ({self.GUIDE_REF})" if self.GUIDE_REF else ""
        self.log_result(f"\n{'='*50}")
        self.log_result(f"{name}{ref}")
        self.log_result("="*50)

    def log_footer(self, result: str = "COMPLETE"):
        """Log a test footer."""
        self.log_result(f"{'='*50}")
        self.log_result(f"{self.TEST_NAME}: {result}")
        self.log_result("="*50)

    # =========================================================================
    # TEST LIFECYCLE
    # =========================================================================

    def start_test(self) -> bool:
        """
        Start a test if none running.

        Returns:
            True if test can start, False if another test is running
        """
        if self.test_running:
            return False
        self.test_running = True
        self.test_abort = False
        return True

    def end_test(self):
        """Mark test as complete."""
        self.test_running = False
        self.test_abort = False

    def abort(self):
        """Signal test to abort."""
        if self.test_running:
            self.test_abort = True
            self.log_result("\n>>> ABORT REQUESTED - stopping spindle...")
            self.hal.send_mdi("M5")

    def check_abort(self) -> bool:
        """Check if test should abort."""
        return self.test_abort

    # =========================================================================
    # SIGNAL SAMPLING
    # =========================================================================

    def sample_signal(self, pin_name: str, duration: float,
                      interval: float = 0.1) -> Tuple[List[float], List[float]]:
        """
        Sample a HAL pin for a given duration.

        Args:
            pin_name: HAL pin name to sample
            duration: Duration to sample in seconds
            interval: Sample interval in seconds

        Returns:
            Tuple of (times, samples) lists
        """
        samples = []
        times = []
        start = time.time()

        while time.time() - start < duration:
            if self.test_abort:
                break
            val = self.hal.get_pin_value(pin_name)
            samples.append(val)
            times.append(time.time() - start)
            time.sleep(interval)

        return times, samples

    def sample_all_signals(self, duration: float,
                           interval: float = 0.1) -> List[Dict]:
        """
        Sample all monitored signals for a duration.

        Args:
            duration: Duration to sample in seconds
            interval: Sample interval in seconds

        Returns:
            List of dictionaries with all values at each sample time
        """
        samples = []
        start = time.time()

        while time.time() - start < duration:
            if self.test_abort:
                break
            values = self.hal.get_all_values()
            values['time'] = time.time() - start
            samples.append(values)
            time.sleep(interval)

        return samples

    # =========================================================================
    # ASSESSMENT METHODS (Guide §7.4)
    # =========================================================================

    def assess_settling(self, settling_time: float) -> str:
        """Assess settling time per Guide §7.4."""
        if settling_time <= TARGETS.settling_excellent:
            return f"EXCELLENT (≤{TARGETS.settling_excellent}s)"
        elif settling_time <= TARGETS.settling_good:
            return f"GOOD (≤{TARGETS.settling_good}s)"
        else:
            return f"SLOW (>{TARGETS.settling_good}s)"

    def assess_overshoot(self, overshoot_pct: float) -> str:
        """Assess overshoot per Guide §7.4."""
        if overshoot_pct <= TARGETS.overshoot_excellent:
            return f"EXCELLENT (≤{TARGETS.overshoot_excellent}%)"
        elif overshoot_pct <= TARGETS.overshoot_good:
            return f"GOOD (≤{TARGETS.overshoot_good}%)"
        else:
            return f"HIGH (>{TARGETS.overshoot_good}%)"

    def assess_ss_error(self, error_rpm: float) -> str:
        """Assess steady-state error per Guide §7.4."""
        abs_error = abs(error_rpm)
        if abs_error <= TARGETS.ss_error_excellent:
            return f"EXCELLENT (≤{TARGETS.ss_error_excellent} RPM)"
        elif abs_error <= TARGETS.ss_error_good:
            return f"GOOD (≤{TARGETS.ss_error_good} RPM)"
        else:
            return f"HIGH (>{TARGETS.ss_error_good} RPM)"

    def assess_recovery(self, recovery_time: float) -> str:
        """Assess load recovery time per Guide §7.4."""
        if recovery_time <= TARGETS.recovery_excellent:
            return f"EXCELLENT (≤{TARGETS.recovery_excellent}s)"
        elif recovery_time <= TARGETS.recovery_good:
            return f"GOOD (≤{TARGETS.recovery_good}s)"
        else:
            return f"SLOW (>{TARGETS.recovery_good}s)"

    def assess_noise(self, noise_rpm: float) -> str:
        """Assess noise/stability per Guide §7.4."""
        if noise_rpm <= TARGETS.noise_excellent:
            return f"EXCELLENT (≤{TARGETS.noise_excellent} RPM)"
        elif noise_rpm <= TARGETS.noise_good:
            return f"GOOD (≤{TARGETS.noise_good} RPM)"
        else:
            return f"HIGH (>{TARGETS.noise_good} RPM)"

    # =========================================================================
    # METRICS CALCULATION
    # =========================================================================

    def calculate_step_metrics(self, start: int, end: int,
                               data: List[Dict]) -> Dict[str, float]:
        """
        Calculate step response metrics.

        Args:
            start: Starting RPM
            end: Target RPM
            data: List of sample dictionaries with 'time' and 'feedback' keys

        Returns:
            Dictionary with rise_time, settling_time, overshoot, ss_error, max_error
        """
        if not data:
            return {
                'rise_time': 0,
                'settling_time': 0,
                'overshoot': 0,
                'ss_error': 0,
                'max_error': 0,
            }

        metrics = DataLogger().calculate_step_metrics(start, end, data)

        return {
            'rise_time': metrics.rise_time_s if metrics.rise_time_s >= 0 else 0,
            'settling_time': metrics.settling_time_s if metrics.settling_time_s >= 0 else 0,
            'overshoot': metrics.overshoot_pct,
            'ss_error': metrics.steady_state_error,
            'max_error': metrics.max_error,
        }

    def calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate basic statistics for a list of values.

        Args:
            values: List of numeric values

        Returns:
            Dictionary with min, max, avg, range, std_dev
        """
        if not values:
            return {'min': 0, 'max': 0, 'avg': 0, 'range': 0, 'std_dev': 0}

        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)

        return {
            'min': min(values),
            'max': max(values),
            'avg': avg,
            'range': max(values) - min(values),
            'std_dev': variance ** 0.5,
        }
