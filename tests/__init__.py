"""
Spindle Tuner - Tests Module

Individual test modules for spindle PID tuning, organized according to
SPINDLE_PID_TUNING_GUIDE_v5.3.

Test Categories:
  1) Pre-Flight Tests (§5)
  2) Startup Tests (§6)
  3) Performance Tests (§7)
  4) Advanced Tests
"""

from __future__ import annotations

from .base import BaseTest, PerformanceTargets, TARGETS, ProcedureDescription, TestDescription


class _TkUnavailable:
    """Fallback UI placeholder used when tkinter components are unavailable."""

    def __init__(self, *_, **__):
        raise ImportError(
            "Tkinter UI components are unavailable in this environment. "
            "Install/enable tkinter to use TestsTab or checklist widgets."
        )


# Conditionally import UI components that require tkinter
try:
    from .tests_tab import TestsTab
    from .checklists_tab import ChecklistsTab, ChecklistGroup

    HAS_TKINTER = True
except ImportError:
    TestsTab = _TkUnavailable  # type: ignore[misc,assignment]
    ChecklistsTab = _TkUnavailable  # type: ignore[misc,assignment]
    ChecklistGroup = _TkUnavailable  # type: ignore[misc,assignment]
    HAS_TKINTER = False

# Import individual test classes for direct access
from .test_signal_chain import SignalChainTest
from .test_preflight import PreflightTest
from .test_encoder import EncoderTest
from .test_open_loop import OpenLoopTest
from .test_forward import ForwardTest
from .test_reverse import ReverseTest
from .test_rate_limit import RateLimitTest
from .test_step import StepTest
from .test_load import LoadTest
from .test_steadystate import SteadyStateTest
from .test_decel import DecelTest
from .test_ramp import RampTest
from .test_full_suite import FullSuiteTest
from .test_watchdog import WatchdogTest

__all__ = [
    # Feature flags
    "HAS_TKINTER",
    # Main UI components
    "TestsTab",
    "ChecklistsTab",
    "ChecklistGroup",
    # Base classes
    "BaseTest",
    "PerformanceTargets",
    "TARGETS",
    "ProcedureDescription",
    "TestDescription",
    # Individual test classes
    "SignalChainTest",
    "PreflightTest",
    "EncoderTest",
    "OpenLoopTest",
    "ForwardTest",
    "ReverseTest",
    "RateLimitTest",
    "StepTest",
    "LoadTest",
    "SteadyStateTest",
    "DecelTest",
    "RampTest",
    "FullSuiteTest",
    "WatchdogTest",
]
