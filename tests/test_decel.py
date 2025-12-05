"""
Deceleration Test

Measures spindle deceleration behavior and rate.
"""

from __future__ import annotations

import math
import time
from typing import List, Optional, Tuple

from config import MONITOR_PINS
from .base import BaseTest, ProcedureDescription


class DecelTest(BaseTest):
    """Deceleration test."""

    TEST_NAME = "Deceleration Test"
    GUIDE_REF = ""

    TARGET_RPM: int = 1200
    SPINUP_TIMEOUT_S: float = 8.0
    SPINUP_TOLERANCE_PCT: float = 0.05

    SAMPLE_INTERVAL_S: float = 0.05
    MAX_SAMPLE_S: float = 4.0
    STOP_THRESHOLD_RPM: float = 100.0

    @classmethod
    def get_description(cls) -> ProcedureDescription:
        return ProcedureDescription(
            name="Deceleration Test",
            guide_ref="",
            purpose=(
                "Measure the spindle's deceleration behavior when stopping.\n"
                "Verifies that the deceleration rate matches the configured\n"
                "RATE_LIMIT and VFD decel time (P0.12).\n\n"
                "A smooth, controlled deceleration indicates proper rate\n"
                "limiting and reduces mechanical stress."
            ),
            prerequisites=[
                "Basic tests completed",
                "VFD P0.12 (decel time) configured",
                "RATE_LIMIT matches VFD settings",
            ],
            procedure=[
                "1. Click 'Run Test' to begin",
                "2. Spindle accelerates to 1200 RPM",
                "3. Stop command (M5) issued",
                "4. Deceleration profile sampled",
                "5. Decel rate calculated and compared",
            ],
            expected_results=[
                "Smooth deceleration curve",
                "Decel rate ~matches RATE_LIMIT",
                "No abrupt stops or jerks",
                "Stop time ~consistent with VFD P0.12",
            ],
            troubleshooting=[
                "Decel much faster than accel:",
                "  -> Check VFD P0.12 matches P0.11",
                "Decel too slow:",
                "  -> Increase VFD P0.12 if needed",
                "Abrupt stop:",
                "  -> May indicate limit2 issue",
            ],
            safety_notes=[
                "Test starts at 1200 RPM",
                "Spindle stops during test",
            ],
        )

    def run(self) -> None:
        if not self.start_test():
            return
        self.run_sequence(self._sequence)

    def _sequence(self) -> None:
        self.log_header(f"DECELERATION TEST: {self.TARGET_RPM} -> 0 RPM")

        feedback_pin = MONITOR_PINS["feedback"]
        target = float(self.TARGET_RPM)

        self.update_progress(0, f"Accelerating to {self.TARGET_RPM} RPM...")
        self.hal.send_mdi(f"M3 S{self.TARGET_RPM}")
        self.log_result(f"Accelerating to {self.TARGET_RPM} RPM...")

        if not self._wait_reach_speed(feedback_pin, target):
            self.log_result("Timeout waiting for spindle to reach speed.")
            self.log_footer("FAIL")
            return

        if self.check_abort():
            self.log_footer("ABORTED")
            return

        self.log_result("Stopping (M5)...")
        self.update_progress(30, "Sampling deceleration...")
        self.hal.send_mdi("M5")

        times: List[float] = []
        rpms: List[float] = []

        t0 = time.monotonic()
        end_t = t0 + self.MAX_SAMPLE_S
        next_t = t0

        while True:
            if self.check_abort():
                self.log_footer("ABORTED")
                return

            now = time.monotonic()
            if now >= end_t:
                break

            t = now - t0
            try:
                fb = float(self.hal.get_pin_value(feedback_pin))
            except Exception as exc:  # pragma: no cover
                self.log_result(f"WARNING: failed reading feedback: {exc}")
                fb = float("nan")

            if math.isfinite(fb):
                times.append(t)
                rpms.append(fb)
                try:
                    self.logger.log_sample({"time": float(t), "feedback": float(fb)})
                except Exception:
                    pass

            prog = 30 + (t / self.MAX_SAMPLE_S) * 50
            self.update_progress(prog, f"Decelerating... {fb:.0f} RPM" if math.isfinite(fb) else "Decelerating...")

            if math.isfinite(fb) and fb < self.STOP_THRESHOLD_RPM:
                break

            next_t += self.SAMPLE_INTERVAL_S
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)

        self.update_progress(85, "Calculating rate...")

        if len(times) < 2:
            self.log_result("Insufficient data collected.")
            self.log_footer("FAIL")
            return

        stop_time = self._first_time_below(rpms, times, self.STOP_THRESHOLD_RPM)
        decel_rate = self._estimate_decel_rate(times, rpms, stop_time)

        self.log_result("\nResults:")
        if stop_time is not None:
            self.log_result(f" Time to <{self.STOP_THRESHOLD_RPM:.0f} RPM: {stop_time:.2f} s")
        else:
            self.log_result(f" Did not reach <{self.STOP_THRESHOLD_RPM:.0f} RPM within {self.MAX_SAMPLE_S:.1f} s")
        self.log_result(f" Estimated decel rate: {decel_rate:.0f} RPM/s")

        rate_limit = self._read_rate_limit()
        if rate_limit and rate_limit > 0 and decel_rate > 0:
            tolerance = 0.30  # 30% tolerance
            if abs(decel_rate - rate_limit) / rate_limit <= tolerance:
                self.log_result(f" Decel matches RATE_LIMIT ({rate_limit:.0f}) within {tolerance*100:.0f}%")
                self.log_footer("PASS")
            else:
                self.log_result(f" Decel differs from RATE_LIMIT ({rate_limit:.0f})")
                self.log_footer("COMPLETE")
        else:
            self.log_result(" RATE_LIMIT param unavailable or invalid; skipping comparison.")
            self.log_footer("COMPLETE")

        self.update_progress(100, "Complete")

    def _wait_reach_speed(self, feedback_pin: str, target: float) -> bool:
        """Wait until feedback reaches target within tolerance, or timeout."""
        deadline = time.monotonic() + self.SPINUP_TIMEOUT_S
        tol = max(1.0, self.SPINUP_TOLERANCE_PCT * target)
        while time.monotonic() < deadline:
            if self.check_abort():
                return False
            try:
                fb = float(self.hal.get_pin_value(feedback_pin))
            except Exception:
                fb = float("nan")

            if math.isfinite(fb) and (fb >= target - tol):
                return True
            time.sleep(0.1)
        return False

    @staticmethod
    def _first_time_below(rpms: List[float], times: List[float], threshold: float) -> Optional[float]:
        for t, rpm in zip(times, rpms):
            if rpm < threshold:
                return float(t)
        return None

    @staticmethod
    def _estimate_decel_rate(times: List[float], rpms: List[float], stop_time: Optional[float]) -> float:
        """
        Estimate decel rate using a least-squares line fit (RPM vs time).
        Returns positive RPM/s.
        """
        n = len(times)
        if n < 2:
            return 0.0

        # Use samples up to stop_time (if present) to avoid late noise near 0.
        if stop_time is not None:
            cut = 0
            for i, t in enumerate(times):
                if t <= stop_time:
                    cut = i + 1
            t_use = times[: max(cut, 2)]
            r_use = rpms[: max(cut, 2)]
        else:
            t_use, r_use = times, rpms

        t_mean = sum(t_use) / len(t_use)
        r_mean = sum(r_use) / len(r_use)
        denom = sum((t - t_mean) ** 2 for t in t_use)
        if denom <= 0:
            return 0.0

        slope = sum((t - t_mean) * (r - r_mean) for t, r in zip(t_use, r_use)) / denom  # RPM/s
        return float(max(0.0, -slope))

    def _read_rate_limit(self) -> Optional[float]:
        # NOTE: Keep the legacy param name first, but fall back to common variants.
        for name in ("RateLimit", "RATE_LIMIT", "rate_limit"):
            try:
                v = float(self.hal.get_param(name))
                if math.isfinite(v):
                    return v
            except Exception:
                continue
        return None
