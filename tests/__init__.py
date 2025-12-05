"""
Spindle Tuner - Tests Module

This package contains individual test modules for spindle PID tuning,
organized according to the SPINDLE_PID_TUNING_GUIDE_v5.3.

Test Categories:
    1. Pre-Flight Tests (§5)
       - Signal Chain Check (§5.1)
       - Pre-Flight Check (§5, §14.3)
       - Encoder Verification (§5.2, §12.2)

    2. Startup Tests (§6)
       - Open Loop Check (§6.1)
       - Forward PID Test (§6.2)
       - Reverse PID Test (§6.3)
       - Rate Limit Test (§6.4)

    3. Performance Tests (§7)
       - Step Response (§7.1)
       - Load Recovery (§7.2)
       - Steady-State (§7.3)

    4. Advanced Tests
       - Deceleration Test
       - Full Ramp Test
       - Full Test Suite
       - Watchdog Test (Mock)
"""

from .base import BaseTest, PerformanceTargets, TARGETS, ProcedureDescription, TestDescription


class _TkUnavailable:
    """Fallback UI placeholder used when tkinter components are unavailable."""

    def __init__(self, *_, **__):
        raise ImportError(
            "Tkinter UI components are unavailable in this environment; "
            "install tkinter to use TestsTab or checklist widgets."
        )


# Conditionally import UI components that require tkinter
try:
    from .tests_tab import TestsTab
    from .checklists_tab import ChecklistsTab, ChecklistWidget
    _HAS_TKINTER = True
except ImportError:
    TestsTab = _TkUnavailable
    ChecklistsTab = _TkUnavailable
    ChecklistWidget = _TkUnavailable
    _HAS_TKINTER = False

# Import individual test classes for direct access using relative imports
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
    # Main UI components
    'TestsTab',
    'ChecklistsTab',
    'ChecklistWidget',

    # Base classes
    'BaseTest',
    'PerformanceTargets',
    'TARGETS',
    'ProcedureDescription',
    'TestDescription',

    # Individual test classes
    'SignalChainTest',
    'PreflightTest',
    'EncoderTest',
    'OpenLoopTest',
    'ForwardTest',
    'ReverseTest',
    'RateLimitTest',
    'StepTest',
    'LoadTest',
    'SteadyStateTest',
    'DecelTest',
    'RampTest',
    'FullSuiteTest',
    'WatchdogTest',
]
