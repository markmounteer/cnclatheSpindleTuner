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

from tests.base import BaseTest, PerformanceTargets, TARGETS, TestDescription
from tests.tests_tab import TestsTab
from tests.checklists_tab import ChecklistsTab, ChecklistWidget

# Import individual test classes for direct access
from tests.test_signal_chain import SignalChainTest
from tests.test_preflight import PreflightTest
from tests.test_encoder import EncoderTest
from tests.test_open_loop import OpenLoopTest
from tests.test_forward import ForwardTest
from tests.test_reverse import ReverseTest
from tests.test_rate_limit import RateLimitTest
from tests.test_step import StepTest
from tests.test_load import LoadTest
from tests.test_steadystate import SteadyStateTest
from tests.test_decel import DecelTest
from tests.test_ramp import RampTest
from tests.test_full_suite import FullSuiteTest
from tests.test_watchdog import WatchdogTest

__all__ = [
    # Main UI components
    'TestsTab',
    'ChecklistsTab',
    'ChecklistWidget',

    # Base classes
    'BaseTest',
    'PerformanceTargets',
    'TARGETS',
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
