"""
Spindle Tuner - Base Test Class

Common functionality for all spindle-tuner procedure tests:
- Performance targets (Guide §7.4)
- Signal sampling utilities (with drift correction)
- Assessment helpers
- Test lifecycle management (start/end/abort)
"""

from __future__ import annotations

import logging
import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
)

from logger import PerformanceMetrics


logger = logging.getLogger(__name__)


class HalProtocol(Protocol):
    """Narrow protocol for the HAL interface methods used by procedure tests."""

    def get_pin_value(self, pin_name: str) -> float: ...

    def get_all_values(self) -> Dict[str, float]: ...

    def send_mdi(self, command: str) -> None: ...

    def get_param(self, param_name: str) -> float: ...

    def set_param(self, param_name: str, value: float) -> bool: ...

    def set_mock_fault(self, fault_type: str, enabled: bool) -> None: ...


class DataLoggerProtocol(Protocol):
    """Protocol for data logging backends."""

    def log_sample(self, sample: Dict[str, float]) -> None: ...

    def log_samples(self, samples: Sequence[Dict[str, float]]) -> None: ...


# =============================================================================
# PERFORMANCE TARGETS (Guide §7.4)
# =============================================================================


@dataclass(frozen=True)
class PerformanceTargets:
    """Performance targets from Guide §7.4."""

    settling_excellent: float = 2.0  # seconds
    settling_good: float = 3.0

    overshoot_excellent: float = 5.0  # percent
    overshoot_good: float = 10.0

    ss_error_excellent: float = 8.0  # RPM
    ss_error_good: float = 15.0

    recovery_excellent: float = 2.0  # seconds
    recovery_good: float = 3.0

    noise_excellent: float = 10.0  # RPM peak-to-peak
    noise_good: float = 20.0


TARGETS = PerformanceTargets()


# =============================================================================
# TEST DESCRIPTIONS
# =============================================================================


@dataclass(frozen=True)
class ProcedureDescription:
    """Description and operator instructions for a test."""

    name: str
    guide_ref: str
    purpose: str
    prerequisites: List[str]
    procedure: List[str]
    expected_results: List[str]
    troubleshooting: List[str]
    safety_notes: List[str]


# Backwards compatibility alias maintained for smoke tests and legacy callers
# that referenced TestDescription before the rename to ProcedureDescription.
TestDescription = ProcedureDescription


# =============================================================================
# BASE TEST CLASS
# =============================================================================


class BaseTest(ABC):
    """
    Abstract base class for all spindle procedure tests.

    Provides:
    - Signal sampling
    - Performance assessment
    - Test lifecycle management
    - Minimal UI logging/progress hooks
    """

    TEST_NAME: str = "Base Test"
    GUIDE_REF: str = ""

    def __init__(
        self,
        hal_interface: HalProtocol,
        data_logger: DataLoggerProtocol,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> None:
        self.hal = hal_interface
        self.logger = data_logger
        self.log_callback = log_callback
        self.progress_callback = progress_callback

        self.test_running = False
        self.test_abort = False

        self._started_at: Optional[float] = None  # monotonic timestamp

        # Lock to ensure thread safety when modifying running state
        self._lock = threading.RLock()

    # -------------------------------------------------------------------------
    # REQUIRED OVERRIDES
    # -------------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def get_description(cls) -> ProcedureDescription:
        """Return detailed description of the test."""

    @abstractmethod
    def run(self) -> None:
        """Execute the test sequence."""

    # -------------------------------------------------------------------------
    # LOGGING UTILITIES
    # -------------------------------------------------------------------------

    def log_result(self, text: str) -> None:
        """Log to the UI callback and system logger."""
        logger.info("[%s] %s", self.TEST_NAME, text)
        if self.log_callback:
            self.log_callback(text)

    def update_progress(self, percent: float, message: str = "") -> None:
        """Update UI progress bar."""
        if self.progress_callback:
            self.progress_callback(percent, message)

    def log_header(self, title: Optional[str] = None) -> None:
        name = title or self.TEST_NAME
        ref = f" ({self.GUIDE_REF})" if self.GUIDE_REF else ""
        self.log_result(f"\n{'=' * 50}")
        self.log_result(f"{name}{ref}")
        self.log_result("=" * 50)

    def log_footer(self, result: str = "COMPLETE") -> None:
        self.log_result(f"{'=' * 50}")
        self.log_result(f"{self.TEST_NAME}: {result}")
        self.log_result("=" * 50)

    # -------------------------------------------------------------------------
    # TEST LIFECYCLE
    # -------------------------------------------------------------------------

    def start_test(self) -> bool:
        """
        Mark test as running.

        Returns False if a test is already in progress.
        """

        with self._lock:
            if self.test_running:
                return False
            self.test_running = True
            self.test_abort = False
            self._started_at = time.monotonic()
            return True

    def end_test(self) -> None:
        """Mark test as finished."""
        with self._lock:
            self.test_running = False
            self.test_abort = False
            self._started_at = None

    def safe_stop_spindle(self) -> None:
        """Best-effort spindle stop with error reporting."""

        try:
            self.hal.send_mdi("M5")
        except (RuntimeError, ValueError, Exception) as exc:  # pragma: no cover - hardware safety
            self.log_result(f"CRITICAL: failed to stop spindle via MDI: {exc}")

    def abort(self) -> None:
        """Signal test to abort and immediately attempt to stop the spindle."""

        with self._lock:
            if not self.test_running:
                return
            self.test_abort = True
        self.log_result("\n>>> ABORT REQUESTED - stopping spindle...")
        self.safe_stop_spindle()

    def check_abort(self) -> bool:
        """Check if an abort has been requested."""
        return self.test_abort

    def run_sequence(self, sequence: Callable[[], None]) -> None:
        """Run a test sequence in a background thread with safe cleanup."""

        def _runner() -> None:
            try:
                sequence()
            except Exception as exc:  # pragma: no cover - UI flow
                self.log_result(f"ERROR: {exc}")
                self.log_footer("FAILED")
                raise
            finally:
                self.safe_stop_spindle()
                self.end_test()

        threading.Thread(target=_runner, daemon=True).start()

    # -------------------------------------------------------------------------
    # SIGNAL SAMPLING
    # -------------------------------------------------------------------------

    def _sampling_loop(self, duration: float, interval: float) -> Iterator[float]:
        """Yield elapsed time values while enforcing drift-corrected intervals."""

        if duration <= 0:
            return
        if interval <= 0:
            raise ValueError("interval must be > 0")

        t0 = time.monotonic()
        end_t = t0 + duration
        next_t = t0

        while True:
            if self.check_abort():
                break

            now = time.monotonic()
            if now >= end_t:
                break

            yield now - t0

            next_t += interval
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)

    def sample_signal(
        self,
        pin_name: str,
        duration: float,
        interval: float = 0.1,
    ) -> Tuple[List[float], List[float]]:
        """
        Sample a HAL pin for a given duration.

        Returns:
            (times, samples) where times are seconds since sampling started.
        """

        times: List[float] = []
        samples: List[float] = []

        for elapsed_t in self._sampling_loop(duration, interval):
            try:
                val = float(self.hal.get_pin_value(pin_name))
            except Exception as exc:  # pragma: no cover - UI flow
                self.log_result(f"WARNING: failed reading '{pin_name}': {exc}")
                val = float("nan")

            times.append(elapsed_t)
            samples.append(val)

        return times, samples

    def sample_all_signals(
        self,
        duration: float,
        interval: float = 0.1,
    ) -> List[Dict[str, float]]:
        """
        Sample all monitored signals for a duration.

        Returns:
            A list of dicts. Each dict includes a 'time' key (seconds since start).
        """

        samples: List[Dict[str, float]] = []

        for elapsed_t in self._sampling_loop(duration, interval):
            values = self.hal.get_all_values()
            values["time"] = float(elapsed_t)
            samples.append(values)

        return samples

    # -------------------------------------------------------------------------
    # ASSESSMENT METHODS (Guide §7.4)
    # -------------------------------------------------------------------------

    def assess_settling(self, settling_time: float) -> str:
        if settling_time <= TARGETS.settling_excellent:
            return f"EXCELLENT (≤{TARGETS.settling_excellent}s)"
        if settling_time <= TARGETS.settling_good:
            return f"GOOD (≤{TARGETS.settling_good}s)"
        return f"SLOW (>{TARGETS.settling_good}s)"

    def assess_overshoot(self, overshoot_pct: float) -> str:
        if overshoot_pct <= TARGETS.overshoot_excellent:
            return f"EXCELLENT (≤{TARGETS.overshoot_excellent}%)"
        if overshoot_pct <= TARGETS.overshoot_good:
            return f"GOOD (≤{TARGETS.overshoot_good}%)"
        return f"HIGH (>{TARGETS.overshoot_good}%)"

    def assess_ss_error(self, error_rpm: float) -> str:
        abs_error = abs(error_rpm)
        if abs_error <= TARGETS.ss_error_excellent:
            return f"EXCELLENT (≤{TARGETS.ss_error_excellent} RPM)"
        if abs_error <= TARGETS.ss_error_good:
            return f"GOOD (≤{TARGETS.ss_error_good} RPM)"
        return f"HIGH (>{TARGETS.ss_error_good} RPM)"

    def assess_recovery(self, recovery_time: float) -> str:
        if recovery_time <= TARGETS.recovery_excellent:
            return f"EXCELLENT (≤{TARGETS.recovery_excellent}s)"
        if recovery_time <= TARGETS.recovery_good:
            return f"GOOD (≤{TARGETS.recovery_good}s)"
        return f"SLOW (>{TARGETS.recovery_good}s)"

    def assess_noise(self, noise_rpm: float) -> str:
        if noise_rpm <= TARGETS.noise_excellent:
            return f"EXCELLENT (≤{TARGETS.noise_excellent} RPM)"
        if noise_rpm <= TARGETS.noise_good:
            return f"GOOD (≤{TARGETS.noise_good} RPM)"
        return f"HIGH (>{TARGETS.noise_good} RPM)"

    # -------------------------------------------------------------------------
    # METRICS CALCULATION
    # -------------------------------------------------------------------------

    def calculate_step_metrics(
        self,
        start: float,
        end: float,
        data: Sequence[Dict[str, float]],
        ss_window_s: float = 1.0,
    ) -> PerformanceMetrics:
        """Calculate step response metrics from sampled data."""

        metrics = PerformanceMetrics()
        if not data:
            return metrics

        times = [float(d.get("time", 0.0)) for d in data if "time" in d]
        feedbacks = [float(d.get("feedback", 0.0)) for d in data if "time" in d]

        if not times or not feedbacks:
            return metrics

        step_size = abs(end - start)

        if math.isclose(step_size, 0.0, abs_tol=1e-9):
            final_fb = feedbacks[-1]
            metrics.steady_state_error = end - final_fb
            metrics.max_error = self._calculate_max_error(data, feedbacks, end)
            return metrics

        metrics.rise_time_s = self._calculate_rise_time(times, feedbacks, start, end)
        metrics.settling_time_s = self._calculate_settling_time(times, feedbacks, end, step_size)
        metrics.overshoot_pct = self._calculate_overshoot(feedbacks, start, end, step_size)
        metrics.steady_state_error = self._calculate_steady_state_error(times, feedbacks, end, ss_window_s)
        metrics.max_error = self._calculate_max_error(data, feedbacks, end)

        return metrics

    def _calculate_rise_time(
        self, times: List[float], feedbacks: List[float], start: float, end: float
    ) -> float:
        """Calculate time to go from 10% to 90% of the step."""

        direction = 1 if end > start else -1
        step_delta = end - start

        thr_10 = start + 0.1 * step_delta
        thr_90 = start + 0.9 * step_delta

        t10: Optional[float] = None
        t90: Optional[float] = None

        def crossed(val: float, thr: float) -> bool:
            return val >= thr if direction > 0 else val <= thr

        for t, fb in zip(times, feedbacks):
            if t10 is None and crossed(fb, thr_10):
                t10 = t
            if t10 is not None and t90 is None and crossed(fb, thr_90):
                t90 = t
                break

        return (t90 - t10) if (t10 is not None and t90 is not None) else 0.0

    def _calculate_settling_time(
        self, times: List[float], feedbacks: List[float], target: float, step_size: float
    ) -> float:
        """Calculate time to stay within 2% band of target."""

        tolerance = max(0.02 * step_size, 1.0)
        last_out_of_tol_idx = -1

        for i, fb in enumerate(feedbacks):
            if abs(fb - target) > tolerance:
                last_out_of_tol_idx = i

        if last_out_of_tol_idx == -1:
            return 0.0
        if last_out_of_tol_idx + 1 < len(times):
            return times[last_out_of_tol_idx + 1]
        return times[-1]

    def _calculate_overshoot(
        self, feedbacks: List[float], start: float, target: float, step_size: float
    ) -> float:
        """Calculate percentage overshoot."""

        if target > start:
            peak = max(feedbacks)
            overshoot = peak - target
        else:
            trough = min(feedbacks)
            overshoot = target - trough

        return max(0.0, (overshoot / step_size) * 100.0)

    def _calculate_steady_state_error(
        self, times: List[float], feedbacks: List[float], target: float, window_s: float
    ) -> float:
        """Calculate average error over the last window_s seconds."""

        t_end = times[-1]
        t_start_window = t_end - max(window_s, 0.0)

        tail = [fb for t, fb in zip(times, feedbacks) if t >= t_start_window]
        if not tail:
            tail = [feedbacks[-1]]

        avg_fb = sum(tail) / len(tail)
        return float(target - avg_fb)

    def _calculate_max_error(
        self, data: Sequence[Dict[str, float]], feedbacks: List[float], target: float
    ) -> float:
        """Calculate the maximum absolute error present in the data."""

        if data and "error" in data[0]:
            errors = [abs(float(d.get("error", 0.0))) for d in data]
            return max(errors)
        return max(abs(fb - target) for fb in feedbacks)

    def calculate_statistics(self, values: Sequence[float]) -> Dict[str, float]:
        """Basic stats with a safe empty-handling path."""

        if not values:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "range": 0.0, "std_dev": 0.0}

        vals = [float(v) for v in values]
        avg = sum(vals) / len(vals)
        variance = sum((v - avg) ** 2 for v in vals) / len(vals)

        return {
            "min": min(vals),
            "max": max(vals),
            "avg": avg,
            "range": max(vals) - min(vals),
            "std_dev": math.sqrt(variance),
        }
