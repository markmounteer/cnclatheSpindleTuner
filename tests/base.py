"""
Spindle Tuner - Base Test Class

Common functionality for all spindle-tuner *procedure tests*:
- Performance targets (Guide §7.4)
- Signal sampling utilities
- Assessment helpers
- Test lifecycle management (start/end/abort)
"""

from __future__ import annotations

import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol, Sequence, Tuple

from logger import PerformanceMetrics


class HalProtocol(Protocol):
    """Narrow protocol for the HAL interface methods used by procedure tests."""

    def get_pin_value(self, pin_name: str) -> float: ...

    def get_all_values(self) -> Dict[str, float]: ...

    def send_mdi(self, command: str) -> None: ...


class DataLoggerProtocol(Protocol):
    """Optional protocol – base class only stores it, tests may call it."""

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
class TestDescription:
    """Description and operator instructions for a test."""

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
    ):
        self.hal = hal_interface
        self.logger = data_logger
        self.log_callback = log_callback
        self.progress_callback = progress_callback

        self.test_running = False
        self.test_abort = False

        self._started_at: Optional[float] = None  # monotonic timestamp

    # -------------------------------------------------------------------------
    # REQUIRED OVERRIDES
    # -------------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def get_description(cls) -> TestDescription:
        """Return detailed description of the test."""

    @abstractmethod
    def run(self):
        """Execute the test sequence."""

    # -------------------------------------------------------------------------
    # LOGGING UTILITIES
    # -------------------------------------------------------------------------

    def log_result(self, text: str) -> None:
        if self.log_callback:
            self.log_callback(text)

    def update_progress(self, percent: float, message: str = "") -> None:
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
        """Return False if another test is already running."""

        if self.test_running:
            return False
        self.test_running = True
        self.test_abort = False
        self._started_at = time.monotonic()
        return True

    def end_test(self) -> None:
        self.test_running = False
        self.test_abort = False
        self._started_at = None

    def safe_stop_spindle(self) -> None:
        """Best-effort spindle stop; never raises."""

        try:
            self.hal.send_mdi("M5")
        except Exception:
            # We intentionally swallow exceptions here to make cleanup reliable.
            pass

    def abort(self) -> None:
        """Signal test to abort and attempt to stop the spindle."""

        if not self.test_running:
            return
        self.test_abort = True
        self.log_result("\n>>> ABORT REQUESTED - stopping spindle...")
        self.safe_stop_spindle()

    def check_abort(self) -> bool:
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

    def _sleep_until(self, target_t: float) -> None:
        now = time.monotonic()
        delay = target_t - now
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

        if duration <= 0:
            return [], []
        if interval <= 0:
            raise ValueError("interval must be > 0")

        t0 = time.monotonic()
        end_t = t0 + duration
        next_t = t0

        times: List[float] = []
        samples: List[float] = []

        while True:
            if self.test_abort:
                break

            now = time.monotonic()
            if now >= end_t:
                break

            try:
                val = float(self.hal.get_pin_value(pin_name))
            except Exception as exc:  # pragma: no cover - UI flow
                self.log_result(f"WARNING: failed reading '{pin_name}': {exc}")
                val = float("nan")

            times.append(now - t0)
            samples.append(val)

            next_t += interval
            self._sleep_until(next_t)

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

        if duration <= 0:
            return []
        if interval <= 0:
            raise ValueError("interval must be > 0")

        t0 = time.monotonic()
        end_t = t0 + duration
        next_t = t0

        samples: List[Dict[str, float]] = []

        while True:
            if self.test_abort:
                break

            now = time.monotonic()
            if now >= end_t:
                break

            values = self.hal.get_all_values()
            values["time"] = float(now - t0)
            samples.append(values)

            next_t += interval
            self._sleep_until(next_t)

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
        """
        Calculate step response metrics from sampled data.

        Expects each sample dict to include:
            - 'time' (seconds)
            - 'feedback' (RPM)
        Optionally:
            - 'error' (RPM)
        """

        metrics = PerformanceMetrics()
        if not data:
            return metrics

        times: List[float] = []
        feedbacks: List[float] = []
        errors: List[float] = []

        for d in data:
            if "time" not in d:
                continue
            t = float(d.get("time", 0.0))
            fb = float(d.get("feedback", 0.0))
            times.append(t)
            feedbacks.append(fb)
            if "error" in d:
                errors.append(abs(float(d.get("error", 0.0))))

        if not times or not feedbacks:
            return metrics

        step_size = abs(end - start)
        if math.isclose(step_size, 0.0, abs_tol=1e-9):
            metrics.steady_state_error = end - feedbacks[-1]
            metrics.max_error = max(errors) if errors else abs(end - feedbacks[-1])
            return metrics

        direction = 1 if end > start else -1
        thr_10 = start + 0.1 * (end - start)
        thr_90 = start + 0.9 * (end - start)

        def crossed(val: float, thr: float) -> bool:
            return val >= thr if direction > 0 else val <= thr

        t10: Optional[float] = None
        t90: Optional[float] = None
        for t, fb in zip(times, feedbacks):
            if t10 is None and crossed(fb, thr_10):
                t10 = t
            if t10 is not None and t90 is None and crossed(fb, thr_90):
                t90 = t
                break

        metrics.rise_time_s = (t90 - t10) if (t10 is not None and t90 is not None) else 0.0

        tolerance = max(0.02 * abs(end), 0.02 * step_size, 1.0)

        last_oot = None
        for i, fb in enumerate(feedbacks):
            if abs(fb - end) > tolerance:
                last_oot = i

        if last_oot is None:
            settling_time = 0.0
        elif last_oot + 1 < len(times):
            settling_time = times[last_oot + 1]
        else:
            settling_time = times[-1]

        metrics.settling_time_s = float(settling_time)

        if direction > 0:
            peak = max(feedbacks)
            overshoot = max(0.0, (peak - end) / step_size * 100.0)
        else:
            trough = min(feedbacks)
            overshoot = max(0.0, (end - trough) / step_size * 100.0)

        metrics.overshoot_pct = float(overshoot)

        t_end = times[-1]
        t_start = t_end - max(ss_window_s, 0.0)
        tail = [fb for t, fb in zip(times, feedbacks) if t >= t_start] or [feedbacks[-1]]
        ss_fb = sum(tail) / len(tail)
        metrics.steady_state_error = float(end - ss_fb)

        if errors:
            metrics.max_error = max(errors)
        else:
            metrics.max_error = max(abs(fb - end) for fb in feedbacks)

        return metrics

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
