#!/usr/bin/env python3
"""
Spindle Tuner - Hardware Abstraction Layer

Provides HAL interface (real or mock) and INI file handling.

Improvements in this version:
- Reliable HAL access via halcmd getp/setp
- Robust parsing of HAL values (including TRUE/FALSE bit pins, NaN/Inf rejection)
- Value caching with configurable TTL using monotonic time
- Thread-safe operations
- Proper logging instead of print statements
- Connection state management with auto-reconnect
- Separated MockPhysicsEngine for cleaner simulation
- Comprehensive error handling
- Pin existence validation
- Centralized halcmd invocation helper
- Step snapping for cleaner parameter values
- Safe INI parsing (no interpolation for % signs)
"""

import configparser
import logging
import math
import platform
import random
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import (
    MONITOR_PINS, TUNING_PARAMS, BASELINE_PARAMS,
    UPDATE_INTERVAL_MS, MOTOR_SPECS, VFD_SPECS
)

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# PLATFORM DETECTION
# =============================================================================

IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Check if halcmd is available (only meaningful on Linux)
HAS_HALCMD = False
if IS_LINUX:
    HAS_HALCMD = shutil.which('halcmd') is not None
    if not HAS_HALCMD:
        logger.info("halcmd not found in PATH - will use mock mode")

if IS_WINDOWS:
    logger.info("Running on Windows - will use mock mode")


# =============================================================================
# LINUXCNC IMPORTS
# =============================================================================

try:
    import hal as hal_module
    HAS_HAL_MODULE = True
except ImportError:
    HAS_HAL_MODULE = False
    hal_module = None

try:
    import linuxcnc
    HAS_LINUXCNC = True
except ImportError:
    HAS_LINUXCNC = False
    linuxcnc = None


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class ConnectionState(Enum):
    """HAL connection states."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()
    MOCK = auto()


class SpindleDirection(Enum):
    """Spindle direction."""
    STOPPED = 0
    FORWARD = 1   # M3
    REVERSE = -1  # M4


@dataclass
class CachedValue:
    """Cached pin value with monotonic timestamp."""
    value: float
    timestamp_mono: float
    
    def is_valid(self, ttl_seconds: float) -> bool:
        """Check if cached value is still valid."""
        return (time.monotonic() - self.timestamp_mono) < ttl_seconds


@dataclass 
class MockState:
    """Mock simulation state container."""
    # Spindle state
    rpm: float = 0.0
    rpm_filtered: float = 0.0  # Filtered RPM for PID feedback
    cmd: float = 0.0
    limited_cmd: float = 0.0
    direction: SpindleDirection = SpindleDirection.STOPPED
    last_direction: SpindleDirection = SpindleDirection.FORWARD
    
    # PID state
    error_i: float = 0.0
    prev_error: float = 0.0
    prev_limited_cmd: float = 0.0
    
    # Physical state
    load_pct: float = 0.0
    thermal_factor: float = 1.0
    time_running: float = 0.0
    revolutions: float = 0.0
    
    # Fault simulation
    encoder_fault: bool = False
    polarity_reversed: bool = False
    dpll_disabled: bool = False
    vfd_fault: bool = False
    estop_triggered: bool = False
    
    # Tuning parameters (can be modified during simulation)
    params: Dict[str, float] = field(default_factory=lambda: BASELINE_PARAMS.copy())


@dataclass
class PhysicsParameters:
    """Configurable physics simulation parameters."""
    vfd_delay_s: float = field(default_factory=lambda: VFD_SPECS['transport_delay_s'])
    max_noise_rpm: float = 3.0
    low_speed_noise_rpm: float = 15.0
    slip_cold_pct: float = field(default_factory=lambda: MOTOR_SPECS['cold_slip_pct'])
    slip_hot_pct: float = field(default_factory=lambda: MOTOR_SPECS['hot_slip_pct'])
    thermal_time_constant_min: float = field(default_factory=lambda: MOTOR_SPECS['thermal_time_const_min'])
    rate_limit_rpm_s: float = field(default_factory=lambda: BASELINE_PARAMS['RateLimit'])
    filter_gain: float = 0.5
    # Max RPM based on VFD max frequency for a 4-pole motor: (120 * max_freq) / 4
    max_rpm: float = field(default_factory=lambda: (120.0 * VFD_SPECS['max_freq_hz']) / 4)


# =============================================================================
# MOCK PHYSICS ENGINE
# =============================================================================

class MockPhysicsEngine:
    """
    Realistic spindle physics simulation based on tuning guide.
    
    Models:
    - VFD rate limiting (limit2 component behavior)
    - Motor slip (load-dependent and thermal)
    - VFD transport delay (~1.5s)
    - PID control loop
    - Encoder noise and DPLL effects
    - Fault conditions
    """
    
    def __init__(self, state: MockState, physics_params: Optional[PhysicsParameters] = None):
        self.state = state
        self.physics = physics_params or PhysicsParameters()
        self._last_update_mono = time.monotonic()
    
    def update(self) -> Dict[str, float]:
        """
        Run one physics simulation step.
        
        Returns dict of all simulated pin values.
        """
        now = time.monotonic()
        dt = min(now - self._last_update_mono, 0.5)  # Cap dt to avoid large jumps
        self._last_update_mono = now

        if dt <= 0:
            dt = UPDATE_INTERVAL_MS / 1000.0
        
        # Get current state
        target = self.state.cmd
        current_rpm = self.state.rpm
        limited_cmd = self.state.limited_cmd
        params = self.state.params
        
        # === E-STOP HANDLING ===
        if self.state.estop_triggered:
            target = 0.0
            self.state.cmd = 0.0
            # Force direction to stopped so downstream math (e.g., revolutions)
            # doesn't continue accumulating with the previous sign.
            self.state.direction = SpindleDirection.STOPPED
        
        # === THERMAL TRACKING (exponential model) ===
        thermal_tau = max(1e-6, self.physics.thermal_time_constant_min * 60)  # seconds
        max_thermal_factor = 1.0 + (self.physics.slip_hot_pct - self.physics.slip_cold_pct) / 100
        
        if target > 0:
            self.state.time_running += dt
            self.state.thermal_factor = 1.0 + (max_thermal_factor - 1.0) * (1.0 - math.exp(-self.state.time_running / thermal_tau))
        else:
            # Cool down faster (convection increases when spindle stops)
            self.state.time_running = max(0, self.state.time_running - dt * 2)
            self.state.thermal_factor = 1.0 + (max_thermal_factor - 1.0) * (1.0 - math.exp(-self.state.time_running / thermal_tau))
        
        # === RATE LIMITING (limit2 simulation) ===
        # Use params (user-adjustable) with physics default as fallback
        rate_limit = params.get('RateLimit', self.physics.rate_limit_rpm_s)
        max_change = rate_limit * dt
        
        if target > limited_cmd:
            limited_cmd = min(target, limited_cmd + max_change)
        elif target < limited_cmd:
            # Decel can be faster than accel
            limited_cmd = max(target, limited_cmd - max_change * 1.5)
        
        self.state.limited_cmd = limited_cmd
        
        # === MOTOR SLIP CALCULATION ===
        base_slip = self.physics.slip_cold_pct / 100.0
        load_slip = (self.state.load_pct / 100.0) * 0.024
        thermal_slip = (self.state.thermal_factor - 1.0) * 0.03
        total_slip = base_slip + load_slip + thermal_slip

        # === VFD DYNAMICS ===
        vfd_delay = max(1e-6, self.physics.vfd_delay_s)
        alpha = min(0.3, dt / (vfd_delay / 3.0))

        # VFD fault slows response
        if self.state.vfd_fault:
            alpha *= 0.1

        # === PID SIMULATION ===
        FF0 = params.get('FF0', 1.0)
        FF1 = params.get('FF1', 0.35)
        P = params.get('P', 0.1)
        I = params.get('I', 1.0)
        D = params.get('D', 0.0)
        max_error_i = params.get('MaxErrorI', 60.0)

        # Use filtered feedback to align with actual PID component behavior
        error = limited_cmd - self.state.rpm_filtered
        p_term = P * error

        self.state.error_i += error * dt * I
        self.state.error_i = max(-max_error_i, min(max_error_i, self.state.error_i))

        d_term = 0.0
        if D:
            d_term = D * (error - self.state.prev_error) / max(dt, 1e-6)
        self.state.prev_error = error

        ff1_term = FF1 * (limited_cmd - self.state.prev_limited_cmd) / max(dt, 1e-6)
        self.state.prev_limited_cmd = limited_cmd

        pid_correction = p_term + self.state.error_i + d_term
        vfd_output = limited_cmd * FF0 + ff1_term + pid_correction

        # === FINAL MOTOR RESPONSE ===
        motor_target = vfd_output * (1.0 - total_slip)

        if self.state.vfd_fault:
            current_rpm = current_rpm * 0.95  # Rapid decel on fault
        else:
            current_rpm = current_rpm * (1 - alpha) + motor_target * alpha
        
        # === ENCODER SIMULATION WITH FILTERING ===
        base_noise = random.gauss(0, self.physics.max_noise_rpm / 3) if not self.state.encoder_fault else 0
        dpll_noise = 0.0
        
        if self.state.dpll_disabled and current_rpm < 200:
            dpll_noise = random.gauss(0, self.physics.low_speed_noise_rpm)
        
        noise = base_noise + dpll_noise
        
        # Apply faults
        if self.state.encoder_fault:
            current_rpm = 0.0
            noise = 0.0
        
        current_rpm = max(0, min(self.physics.max_rpm, current_rpm))
        self.state.rpm = current_rpm

        # Measurement before filtering (clamped to avoid negative/invalid readings)
        measured_rpm = max(0.0, min(self.physics.max_rpm, current_rpm + noise))
        
        # Low-pass filter on feedback (simulates actual filtering in HAL)
        # Use params (user-adjustable) with physics default as fallback
        # Clamp to valid range [0.1, 1.0] to prevent filter freezing (0 = no update)
        filter_gain = params.get('FilterGain', self.physics.filter_gain)
        filter_gain = max(0.1, min(1.0, filter_gain))
        self.state.rpm_filtered = (
            self.state.rpm_filtered * (1 - filter_gain)
            + measured_rpm * filter_gain
        )

        # === REVOLUTIONS TRACKING ===
        rps = current_rpm / 60.0
        if self.state.direction != SpindleDirection.STOPPED:
            self.state.last_direction = self.state.direction

        active_direction = self.state.direction
        if active_direction == SpindleDirection.STOPPED and current_rpm > 1.0:
            active_direction = self.state.last_direction

        dir_mult = active_direction.value if active_direction != SpindleDirection.STOPPED else 0
        command_dir = (
            active_direction.value
            if active_direction != SpindleDirection.STOPPED
            else self.state.last_direction.value
        )
        self.state.revolutions += rps * dt * dir_mult
        
        # === BUILD OUTPUT VALUES ===
        polarity_mult = -1 if self.state.polarity_reversed else 1
        filtered_rpm = self.state.rpm_filtered
        signed_rpm = filtered_rpm * dir_mult * polarity_mult
        # Keep raw feedback aligned with filtered feedback for deterministic mock tests
        signed_rpm_raw = signed_rpm
        abs_rpm = abs(signed_rpm)
        encoder_scale = -4096 if self.state.polarity_reversed else 4096
        signed_cmd_raw = target * command_dir
        signed_cmd_limited = limited_cmd * command_dir
        
        at_speed = abs(limited_cmd - filtered_rpm) < params.get('Deadband', 10) * 2
        external_ok = 0.0 if (self.state.encoder_fault or self.state.vfd_fault or 
                              self.state.estop_triggered) else 1.0
        
        outputs: Dict[str, float] = {}

        def add_if_present(key: str, value: float):
            pin_name = MONITOR_PINS.get(key)
            if pin_name:
                outputs[pin_name] = value

        # Command path
        add_if_present('cmd_raw', signed_cmd_raw)
        add_if_present('cmd_limited', signed_cmd_limited)

        # Feedback path (uses filtered RPM)
        add_if_present('feedback', signed_rpm)
        add_if_present('feedback_raw', signed_rpm_raw)
        add_if_present('feedback_abs', abs_rpm)

        # PID internals
        signed_error = signed_cmd_limited - signed_rpm
        add_if_present('error', signed_error)
        add_if_present('errorI', self.state.error_i)
        add_if_present('output', vfd_output)

        # Status
        add_if_present('at_speed', 1.0 if at_speed else 0.0)
        add_if_present('watchdog', 1.0 if limited_cmd > 50 else 0.0)
        add_if_present('encoder_fault', 1.0 if self.state.encoder_fault else 0.0)
        add_if_present('spindle_on', 1.0 if target > 0 else 0.0)

        # Threading
        add_if_present('spindle_revs', self.state.revolutions)

        # Hardware status / safety pins
        add_if_present('dpll_timer', 0.0 if self.state.dpll_disabled else 100.0)
        add_if_present('external_ok', external_ok)
        add_if_present('safety_chain', external_ok)
        add_if_present('encoder_scale', encoder_scale)

        return outputs


# =============================================================================
# HAL INTERFACE
# =============================================================================

class HalInterface:
    """
    Hardware abstraction layer for LinuxCNC HAL.
    
    Features:
    - Automatic selection of fastest available interface
    - Value caching for performance
    - Thread-safe operations
    - Connection state management
    - Mock mode with realistic physics
    
    Usage:
        hal = HalInterface()  # Auto-detect mode
        hal = HalInterface(mock=True)  # Force mock mode
        
        # Read values
        rpm = hal.get_pin_value('spindle-vel-fb-rpm')
        values = hal.get_all_values()
        
        # Write values
        hal.set_param('P', 0.15)
        
        # Send commands
        hal.send_mdi('M3 S1000')
    """
    
    # Cache TTL in seconds
    CACHE_TTL = 0.05  # 50ms cache validity
    
    def __init__(self, mock: bool = False):
        """
        Initialize HAL interface.
        
        Args:
            mock: Force mock mode even if HAL is available
        """
        self._lock = threading.RLock()
        self._cache: Dict[str, CachedValue] = {}
        self._validated_pins: set = set()
        
        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._last_error: Optional[str] = None
        self._connect_attempts = 0
        
        # LinuxCNC interfaces
        self._hal_component = None
        self._linuxcnc_cmd = None
        self._linuxcnc_stat = None
        
        # Mock mode
        self._mock_state = MockState()
        self._physics_params = PhysicsParameters()
        self._physics_engine: Optional[MockPhysicsEngine] = None
        self._mock_values: Dict[str, float] = {}
        self._mock_last_update_mono: float = 0.0
        self._mock_update_interval = UPDATE_INTERVAL_MS / 1000.0
        self._forced_mock = False
        
        # Performance tracking
        self._read_times: List[float] = []
        self._max_read_times = 100  # Keep last N read times
        
        # Resolve halcmd path once at init
        self._halcmd_path = shutil.which('halcmd') or 'halcmd'
        
        # Determine mode - use mock if:
        # 1. Explicitly requested (mock=True)
        # 2. Running on Windows (no LinuxCNC support)
        # 3. halcmd not available on Linux
        # Note: We do NOT require the Python hal/linuxcnc modules since
        # the primary interface is halcmd getp/setp. The Python modules
        # are only needed for MDI commands via linuxcnc.command().
        use_mock = (
            mock or
            IS_WINDOWS or
            not HAS_HALCMD
        )

        self._forced_mock = mock or IS_WINDOWS or not HAS_HALCMD

        if use_mock:
            self._init_mock_mode()
        else:
            self._connect()
    
    @property
    def is_mock(self) -> bool:
        """Check if running in mock mode."""
        return self._state == ConnectionState.MOCK
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to HAL."""
        return self._state == ConnectionState.CONNECTED
    
    @property
    def connection_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error
    
    @property
    def mock_state(self) -> MockState:
        """Get mock state (for external manipulation)."""
        return self._mock_state
    
    @property
    def physics_params(self) -> PhysicsParameters:
        """Get physics simulation parameters (for customization)."""
        return self._physics_params
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get HAL read performance statistics.
        
        Returns:
            Dict with avg_read_time_ms, max_read_time_ms, sample_count
        """
        with self._lock:
            if not self._read_times:
                return {'avg_read_time_ms': 0.0, 'max_read_time_ms': 0.0, 'sample_count': 0}

            avg_time = sum(self._read_times) / len(self._read_times) * 1000
            max_time = max(self._read_times) * 1000

        return {
            'avg_read_time_ms': round(avg_time, 2),
            'max_read_time_ms': round(max_time, 2),
            'sample_count': len(self._read_times)
        }
    
    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    
    def _init_mock_mode(self):
        """Initialize mock mode."""
        logger.info("Initializing mock mode")
        self._state = ConnectionState.MOCK
        self._physics_engine = MockPhysicsEngine(self._mock_state, self._physics_params)
        self._mock_last_update_mono = 0.0
    
    def _run_halcmd(self, args: List[str], *, timeout: float = 1.0) -> subprocess.CompletedProcess:
        """
        Run halcmd with given arguments.
        
        Args:
            args: Command arguments (e.g., ['-s', 'getp', 'pin.name'])
            timeout: Command timeout in seconds
            
        Returns:
            CompletedProcess result
        """
        return subprocess.run(
            [self._halcmd_path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    
    def _verify_halcmd_connection(self) -> bool:
        """
        Verify that halcmd can actually communicate with a running HAL instance.

        Returns:
            True if halcmd can talk to HAL, False otherwise
        """
        try:
            # Use 'halcmd show' to verify HAL is running and accessible
            # This command lists components and should always work if HAL is up
            result = self._run_halcmd(['show', 'comp'], timeout=2.0)
            if result.returncode == 0:
                logger.debug("halcmd verification successful")
                return True
            else:
                logger.warning(f"halcmd verification failed: {result.stderr or 'no output'}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning("halcmd verification timed out")
            return False
        except Exception as e:
            logger.warning(f"halcmd verification error: {e}")
            return False

    def _connect(self) -> bool:
        """Connect to LinuxCNC HAL."""
        with self._lock:
            self._state = ConnectionState.CONNECTING
            self._connect_attempts += 1

            # First, verify halcmd can actually talk to HAL
            # This is the primary interface - Python modules are optional
            if not self._verify_halcmd_connection():
                self._last_error = "halcmd cannot communicate with HAL (is LinuxCNC running?)"
                logger.error(self._last_error)
                self._state = ConnectionState.ERROR
                # Fall back to mock mode
                self._init_mock_mode()
                return False

            try:
                # Try LinuxCNC command interface for MDI support (optional)
                if HAS_LINUXCNC:
                    try:
                        self._linuxcnc_cmd = linuxcnc.command()
                        self._linuxcnc_stat = linuxcnc.stat()
                        self._linuxcnc_stat.poll()
                        logger.info("Connected to LinuxCNC command interface (MDI available)")
                    except Exception as e:
                        # MDI won't work, but halcmd I/O is still fine
                        logger.warning(f"LinuxCNC command interface unavailable: {e}")
                        self._linuxcnc_cmd = None
                        self._linuxcnc_stat = None

                # halcmd verification passed - we're connected
                self._state = ConnectionState.CONNECTED
                self._last_error = None
                logger.info("Connected to HAL via halcmd")
                return True

            except Exception as e:
                self._last_error = str(e)
                logger.error(f"HAL connection failed: {e}")
                self._state = ConnectionState.ERROR

                # Fall back to mock mode
                self._init_mock_mode()
                return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to HAL."""
        if self._state == ConnectionState.MOCK and self._forced_mock:
            return False
        return self._connect()
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get connection diagnostics."""
        with self._lock:
            return {
                'state': self._state.name,
                'is_mock': self.is_mock,
                'platform': platform.system(),
                'is_windows': IS_WINDOWS,
                'is_linux': IS_LINUX,
                'has_halcmd': HAS_HALCMD,
                'has_hal_module': HAS_HAL_MODULE,
                'has_linuxcnc': HAS_LINUXCNC,
                'connect_attempts': self._connect_attempts,
                'last_error': self._last_error,
                'cache_size': len(self._cache),
                'validated_pins': len(self._validated_pins),
            }
    
    # -------------------------------------------------------------------------
    # Pin Reading
    # -------------------------------------------------------------------------
    
    def get_pin_value(self, pin_name: str, use_cache: bool = True) -> float:
        """
        Get value from a HAL pin.
        
        Args:
            pin_name: Full HAL pin name
            use_cache: Whether to use cached values
            
        Returns:
            Pin value as float
        """
        if not pin_name:
            logger.warning("Empty pin name provided to get_pin_value")
            return 0.0

        with self._lock:
            # Check cache
            if use_cache and pin_name in self._cache:
                cached = self._cache[pin_name]
                if cached.is_valid(self.CACHE_TTL):
                    return cached.value
            
            # Get value
            if self.is_mock:
                value = self._get_mock_value(pin_name)
            else:
                value = self._read_hal_pin(pin_name)
            
            # Update cache
            self._cache[pin_name] = CachedValue(value, time.monotonic())
            
            return value
    
    def _get_mock_value(self, pin_name: str) -> float:
        """Get simulated value for pin. Thread-safe via RLock."""
        with self._lock:
            self._update_mock_values()
            return self._mock_values.get(pin_name, 0.0)

    def _update_mock_values(self):
        """
        Update mock physics at most once per configured interval.

        Note: Caller MUST hold self._lock before calling this method.
        This method is not thread-safe on its own.
        """
        if not self._physics_engine:
            return

        update_start = time.monotonic()
        if (update_start - self._mock_last_update_mono) >= self._mock_update_interval:
            self._mock_values = self._physics_engine.update()
            # Use the captured timestamp to avoid cadence jitter from update duration
            self._mock_last_update_mono = update_start
    
    @staticmethod
    def _parse_hal_value(text: str) -> float:
        """
        Parse HAL pin/signal value from halcmd output.
        
        Handles:
        - Numeric values (float, int)
        - Boolean bit pins: TRUE/FALSE, ON/OFF, YES/NO
        - Rejects NaN and Inf values
        """
        s = text.strip().upper()
        if not s:
            raise ValueError("Empty HAL value")
        
        # Handle boolean bit pins
        if s in ('TRUE', 'ON', 'YES'):
            return 1.0
        if s in ('FALSE', 'OFF', 'NO'):
            return 0.0
        
        # Handle numeric values
        val = float(text.strip())
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Non-finite HAL value: {text.strip()}")
        return val
    
    def _read_hal_pin(self, pin_name: str) -> float:
        """Read pin value from real HAL."""
        try:
            result = self._run_halcmd(['-s', 'getp', pin_name], timeout=1.0)
            
            if result.returncode == 0:
                return self._parse_hal_value(result.stdout)
            else:
                logger.warning(f"halcmd error for {pin_name}: {result.stderr}")
                return 0.0
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout reading {pin_name}")
            return 0.0
        except ValueError as e:
            logger.error(f"Invalid value for {pin_name}: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error reading {pin_name}: {e}")
            return 0.0

    def _read_hal_pins_bulk(self, pin_names: List[str]) -> Dict[str, float]:
        """
        Read multiple pins in a single halcmd invocation.

        Uses 'getp' commands fed via stdin to a single halcmd process.
        This is more reliable than 'show pin' which has variable output
        format (connected pins include arrows and signal names).
        """
        if not pin_names:
            return {}

        values: Dict[str, float] = {}

        # Deduplicate while preserving order
        pin_list = list(dict.fromkeys(pin_names))

        # Build getp commands - one per line, fed via stdin
        # Using -s flag for terse (single value) output per command
        commands = [f"getp {pin}" for pin in pin_list]
        cmd_str = "\n".join(commands)

        try:
            timeout = max(2.0, len(pin_list) * 0.15)
            result = subprocess.run(
                [self._halcmd_path, '-s'],
                input=cmd_str,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            logger.error("Timeout reading HAL pins (bulk)")
            return values
        except Exception as e:
            logger.error(f"Error running bulk halcmd: {e}")
            return values

        # Note: halcmd may return non-zero if ANY pin fails, but we still
        # want to parse successful outputs. Log warning but continue.
        if result.returncode != 0 and not result.stdout.strip():
            logger.warning(f"halcmd bulk read failed: {result.stderr}")
            return values

        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]

        # Parse results - with -s flag, each getp outputs exactly one line
        # If a pin doesn't exist, halcmd prints an error to stderr and
        # may skip that output line. When this happens, we cannot reliably
        # map output lines to pins since we don't know which pin failed.
        if len(lines) != len(pin_list):
            # Line count mismatch - positional mapping is unsafe, fall back
            # to individual reads
            logger.debug(
                f"Bulk read output mismatch ({len(lines)} lines for "
                f"{len(pin_list)} pins); falling back to individual reads"
            )
            for pin in pin_list:
                values[pin] = self._read_hal_pin(pin)
            if values:
                with self._lock:
                    now = time.monotonic()
                    for pin, val in values.items():
                        self._cache[pin] = CachedValue(val, now)
            return values

        # Log stderr if present (may contain warnings) but continue if
        # line count matches - the values are likely still valid
        if result.stderr.strip():
            logger.debug(f"halcmd bulk read stderr (continuing): {result.stderr.strip()}")

        try:
            parsed_values = [self._parse_hal_value(line.strip()) for line in lines]
        except Exception as e:
            logger.error(f"Failed to parse bulk HAL output: {e}; falling back to individual reads")
            for pin in pin_list:
                values[pin] = self._read_hal_pin(pin)
            if values:
                with self._lock:
                    now = time.monotonic()
                    for pin, val in values.items():
                        self._cache[pin] = CachedValue(val, now)
            return values

        for pin, parsed in zip(pin_list, parsed_values):
            values[pin] = parsed

        if values:
            with self._lock:
                now = time.monotonic()  # Capture inside lock for consistency
                for pin, val in values.items():
                    self._cache[pin] = CachedValue(val, now)

        return values
    
    def get_all_values(self) -> Dict[str, float]:
        """
        Get all monitored pin values.
        
        Returns:
            Dict mapping pin keys to values
        """
        start_time = time.monotonic()
        values = {}

        if self.is_mock:
            # Single physics update for all values
            with self._lock:
                self._update_mock_values()
                for key, pin in MONITOR_PINS.items():
                    values[key] = self._mock_values.get(pin, 0.0)
        else:
            # Map unique pins to their keys to avoid duplicate reads
            pin_map: Dict[str, List[str]] = {}
            for key, pin in MONITOR_PINS.items():
                pin_map.setdefault(pin, []).append(key)

            # Bulk read pins to minimize halcmd calls
            bulk_values = self._read_hal_pins_bulk(list(pin_map.keys()))

            for pin, keys in pin_map.items():
                val = bulk_values.get(pin)
                if val is None:
                    # Fallback to individual read if missing from bulk output
                    val = self.get_pin_value(pin, use_cache=False)
                for key in keys:
                    values[key] = val

        # Track performance
        elapsed = time.monotonic() - start_time
        with self._lock:
            self._read_times.append(elapsed)
            if len(self._read_times) > self._max_read_times:
                self._read_times.pop(0)

        return values
    
    def get_param(self, param_name: str) -> float:
        """
        Get current value of a tuning parameter.
        
        Args:
            param_name: Parameter name (e.g., 'P', 'I', 'FF1')
            
        Returns:
            Parameter value
        """
        if param_name not in TUNING_PARAMS:
            logger.warning(f"Unknown parameter: {param_name}")
            return 0.0
        
        if self.is_mock:
            with self._lock:
                return self._mock_state.params.get(
                    param_name,
                    BASELINE_PARAMS.get(param_name, 0.0)
                )

        meta = TUNING_PARAMS[param_name]
        if not meta or not meta[0]:
            logger.warning(f"No HAL pin configured for parameter: {param_name}")
            return BASELINE_PARAMS.get(param_name, 0.0)

        pin_name = meta[0]
        return self.get_pin_value(pin_name, use_cache=False)
    
    def get_all_params(self) -> Dict[str, float]:
        """Get all tuning parameter values."""
        return {name: self.get_param(name) for name in TUNING_PARAMS}
    
    # -------------------------------------------------------------------------
    # Pin Writing
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _clamp_and_snap(value: float, min_val: float, max_val: float, step: float) -> float:
        """
        Clamp value to range and snap to nearest step.
        
        Args:
            value: Input value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            step: Step size (0 to disable snapping)
            
        Returns:
            Clamped and snapped value
        """
        v = max(min_val, min(max_val, value))
        if step and step > 0:
            # Snap to nearest step relative to min_val
            steps = round((v - min_val) / step)
            v = min_val + steps * step
            v = max(min_val, min(max_val, v))
        return v

    @staticmethod
    def _get_param_bounds(param_name: str) -> Tuple[float, float, float]:
        """Safely extract min, max, and step from TUNING_PARAMS with defaults."""
        meta = TUNING_PARAMS.get(param_name, [])
        min_val = meta[2] if len(meta) > 2 else float('-inf')
        max_val = meta[3] if len(meta) > 3 else float('inf')
        step = meta[4] if len(meta) > 4 else 0.0
        return float(min_val), float(max_val), float(step)
    
    def set_param(self, param_name: str, value: float) -> bool:
        """
        Set a tuning parameter value.
        
        Args:
            param_name: Parameter name
            value: New value
            
        Returns:
            True if successful
        """
        if param_name not in TUNING_PARAMS:
            logger.warning(f"Unknown parameter: {param_name}")
            return False

        try:
            value = float(value)
        except (TypeError, ValueError):
            logger.error(f"Invalid value type for {param_name}: {value}")
            return False

        if math.isnan(value) or math.isinf(value):
            logger.error(f"Non-finite value for {param_name}: {value}")
            return False

        # Validate and snap to range/step
        min_val, max_val, step = self._get_param_bounds(param_name)
        original_value = value
        value = self._clamp_and_snap(value, min_val, max_val, step)
        if value != original_value:
            logger.debug(f"Adjusted {param_name} from {original_value} -> {value} (range/step)")

        if self.is_mock:
            with self._lock:
                self._mock_state.params[param_name] = value
            logger.debug(f"[MOCK] Set {param_name} = {value}")
            return True

        try:
            meta = TUNING_PARAMS[param_name]
            if not meta or not meta[0]:
                logger.error(f"No HAL pin configured for parameter: {param_name}")
                return False

            pin_name = meta[0]
            result = self._run_halcmd(['setp', pin_name, str(value)], timeout=2.0)
            
            if result.returncode == 0:
                # Invalidate cache
                with self._lock:
                    if pin_name in self._cache:
                        del self._cache[pin_name]
                logger.info(f"Set {param_name} = {value}")
                return True
            else:
                logger.error(f"halcmd error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set {param_name}: {e}")
            return False
    
    def set_params(self, params: Dict[str, float]) -> Dict[str, bool]:
        """
        Set multiple parameters at once.
        
        Args:
            params: Dict of parameter names to values
            
        Returns:
            Dict of parameter names to success status
        """
        results = {}
        for name, value in params.items():
            results[name] = self.set_param(name, value)
        return results
    
    def set_params_bulk(self, params: Dict[str, float]) -> bool:
        """
        Set multiple parameters efficiently using a single halcmd process.

        This is faster than set_params() for many parameters as it spawns
        only one subprocess.

        Args:
            params: Dict of parameter names to values

        Returns:
            True if at least one known parameter was set successfully.
            Unknown parameters are ignored (with a warning).
        """
        if not params:
            return True

        # Track unknown parameters (warn but do not fail)
        unknown_params = [name for name in params if name not in TUNING_PARAMS]
        if unknown_params:
            for name in unknown_params:
                logger.warning(f"Unknown parameter in bulk set: {name}")

        if self.is_mock:
            with self._lock:
                updated = 0

                for name, value in params.items():
                    if name not in TUNING_PARAMS:
                        continue

                    try:
                        numeric_value = float(value)
                    except (TypeError, ValueError):
                        logger.error(f"Invalid value type for {name}: {value}")
                        continue

                    if math.isnan(numeric_value) or math.isinf(numeric_value):
                        logger.error(f"Non-finite value for {name}: {numeric_value}")
                        continue

                    min_val, max_val, step = self._get_param_bounds(name)
                    clamped_value = self._clamp_and_snap(numeric_value, min_val, max_val, step)
                    self._mock_state.params[name] = clamped_value
                    updated += 1
                    if clamped_value != numeric_value:
                        logger.debug(
                            f"[MOCK] Adjusted {name} from {numeric_value} -> {clamped_value}"
                        )

            if updated:
                logger.debug(f"[MOCK] Bulk set {updated} params")
            # Success if any known params were set
            return updated > 0

        try:
            # Build commands for stdin
            commands = []
            for param_name, value in params.items():
                if param_name not in TUNING_PARAMS:
                    continue

                # Validate and clamp using the same rules as set_param
                min_val, max_val, step = self._get_param_bounds(param_name)
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    logger.error(f"Invalid value type for {param_name}: {value}")
                    continue

                if math.isnan(value) or math.isinf(value):
                    logger.error(f"Non-finite value for {param_name}: {value}")
                    continue

                value = self._clamp_and_snap(value, min_val, max_val, step)

                meta = TUNING_PARAMS[param_name]
                if not meta or not meta[0]:
                    logger.warning(f"No HAL pin configured for parameter: {param_name}")
                    continue

                pin_name = meta[0]
                commands.append(f"setp {pin_name} {value}")

            if not commands:
                # All params were unknown - already warned above
                return False

            cmd_str = '\n'.join(commands)
            result = subprocess.run(
                [self._halcmd_path],
                input=cmd_str,
                capture_output=True,
                text=True,
                timeout=3.0
            )

            if result.returncode == 0:
                # Invalidate cache for all modified pins
                with self._lock:
                    for param_name in params:
                        if param_name in TUNING_PARAMS:
                            meta = TUNING_PARAMS[param_name]
                            if meta and meta[0]:
                                self._cache.pop(meta[0], None)

                logger.info(f"Bulk set {len(commands)} params")
                return True
            else:
                logger.error(f"halcmd bulk set failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout during bulk param set")
            return False
        except Exception as e:
            logger.error(f"Bulk set params failed: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # MDI Commands
    # -------------------------------------------------------------------------
    
    def send_mdi(self, command: str) -> bool:
        """
        Send MDI command to LinuxCNC.
        
        Args:
            command: G-code or M-code command
            
        Returns:
            True if command was sent successfully
        """
        if self.is_mock:
            return self._mock_mdi(command)
        
        if self._linuxcnc_cmd is None or self._linuxcnc_stat is None:
            logger.error("LinuxCNC command interface not available")
            return False

        try:
            self._linuxcnc_stat.poll()

            # Switch to MDI mode if needed
            if self._linuxcnc_stat.task_mode != linuxcnc.MODE_MDI:
                self._linuxcnc_cmd.mode(linuxcnc.MODE_MDI)
                self._linuxcnc_cmd.wait_complete(2.0)
            
            self._linuxcnc_cmd.mdi(command)
            logger.info(f"Sent MDI: {command}")
            return True
            
        except Exception as e:
            logger.error(f"MDI command failed: {e}")
            self._last_error = str(e)
            return False
    
    def _mock_mdi(self, command: str) -> bool:
        """Handle MDI commands in mock mode."""
        cmd = command.upper().strip()

        if cmd == 'M5':
            with self._lock:
                self._mock_state.cmd = 0.0
                self._mock_state.direction = SpindleDirection.STOPPED
            logger.debug("[MOCK] Spindle STOP")

        elif cmd.startswith('M3'):
            with self._lock:
                self._mock_state.direction = SpindleDirection.FORWARD
                self._mock_state.cmd = self._parse_speed(cmd)
            logger.debug(f"[MOCK] Spindle FWD S{self._mock_state.cmd}")

        elif cmd.startswith('M4'):
            with self._lock:
                self._mock_state.direction = SpindleDirection.REVERSE
                self._mock_state.cmd = self._parse_speed(cmd)
            logger.debug(f"[MOCK] Spindle REV S{self._mock_state.cmd}")
            
        else:
            logger.debug(f"[MOCK] Unknown command: {command}")
        
        return True
    
    @staticmethod
    def _parse_speed(command: str) -> float:
        """Parse speed value from M3/M4 command."""
        if 'S' not in command:
            return 1000.0  # Default speed

        try:
            # Extract everything after 'S' and take the first token
            after_s = command.split('S')[-1].strip()
            if not after_s:
                return 1000.0  # No value after S
            # Handle cases like "S1000" or "S 1000" or "S1000 F100"
            s_val = after_s.split()[0]
            return float(s_val)
        except (IndexError, ValueError):
            return 1000.0  # Default speed on parse failure
    
    # -------------------------------------------------------------------------
    # Mock Mode Control
    # -------------------------------------------------------------------------
    
    def set_mock_load(self, load_pct: float):
        """
        Set simulated cutting load.

        Args:
            load_pct: Load percentage (0-100)
        """
        with self._lock:
            self._mock_state.load_pct = max(0.0, min(100.0, load_pct))
    
    def set_mock_fault(self, fault_type: str, enabled: bool):
        """
        Enable/disable simulated faults.

        Args:
            fault_type: 'encoder', 'polarity', 'dpll', 'vfd', or 'estop'
            enabled: True to enable fault
        """
        with self._lock:
            if fault_type == 'encoder':
                self._mock_state.encoder_fault = enabled
            elif fault_type == 'polarity':
                self._mock_state.polarity_reversed = enabled
            elif fault_type == 'dpll':
                self._mock_state.dpll_disabled = enabled
            elif fault_type == 'vfd':
                self._mock_state.vfd_fault = enabled
            elif fault_type == 'estop':
                self._mock_state.estop_triggered = enabled
                if enabled:
                    # E-stop immediately stops spindle command
                    self._mock_state.cmd = 0.0
            else:
                logger.warning(f"Unknown fault type: {fault_type}")
        
        logger.debug(f"[MOCK] {fault_type} fault: {enabled}")
    
    def reset_mock_state(self):
        """Reset mock state to defaults. Thread-safe."""
        with self._lock:
            self._mock_state = MockState()
            if self._physics_engine:
                self._physics_engine.state = self._mock_state
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def clear_cache(self):
        """Clear the value cache."""
        with self._lock:
            self._cache.clear()
    
    def validate_pin(self, pin_name: str) -> bool:
        """
        Check if a pin exists in HAL.
        
        Args:
            pin_name: Full pin name
            
        Returns:
            True if pin exists
        """
        if self.is_mock:
            return True

        with self._lock:
            if pin_name in self._validated_pins:
                return True

        try:
            # Use getp - it gives a clear success/failure signal
            # Unlike 'show pin', getp returns non-zero if pin doesn't exist
            result = self._run_halcmd(['-s', 'getp', pin_name], timeout=1.0)
            exists = result.returncode == 0

            if exists:
                with self._lock:
                    self._validated_pins.add(pin_name)

            return exists
            
        except Exception:
            return False
    
    @staticmethod
    def rpm_to_hz(rpm: float, poles: int = 4) -> float:
        """Convert RPM to electrical frequency (Hz)."""
        return (rpm * poles) / 120.0
    
    @staticmethod
    def hz_to_rpm(hz: float, poles: int = 4) -> float:
        """Convert electrical frequency (Hz) to RPM."""
        return (hz * 120.0) / poles


# =============================================================================
# INI FILE HANDLER
# =============================================================================

class IniFileHandler:
    """
    Handles reading/writing LinuxCNC INI file sections.
    
    Provides:
    - Section reading with type conversion
    - Safe INI generation (doesn't overwrite)
    - Parameter mapping to HAL pins
    - INI file backup before modifications
    """
    
    def __init__(self, ini_path: Optional[Path] = None):
        """
        Initialize INI handler.
        
        Args:
            ini_path: Path to INI file (optional)
        """
        self.ini_path = Path(ini_path) if ini_path else None
        self.backup_dir = Path.home() / ".spindle_tuner_backups"
    
    def backup_ini_file(self) -> Optional[Path]:
        """
        Create a timestamped backup of the INI file.
        
        Returns:
            Path to backup file, or None if backup failed
        """
        if not self.ini_path or not self.ini_path.exists():
            logger.warning("No INI file to backup")
            return None
        
        try:
            # Create backup directory if needed
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped backup name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.ini_path.stem}.backup_{timestamp}{self.ini_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copy file
            shutil.copy2(self.ini_path, backup_path)
            
            logger.info(f"INI backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to backup INI file: {e}")
            return None
    
    def list_backups(self) -> List[Path]:
        """
        List available INI backups.
        
        Returns:
            List of backup file paths, sorted newest first
        """
        if not self.backup_dir.exists():
            return []
        
        backups = list(self.backup_dir.glob("*.backup_*"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups
    
    def read_section(self, section_name: str = 'SPINDLE_0') -> Dict[str, Any]:
        """
        Read a section from INI file using configparser.
        
        Args:
            section_name: Section name (without brackets)
            
        Returns:
            Dict of key-value pairs
        """
        if not self.ini_path or not self.ini_path.exists():
            logger.warning(f"INI file not found: {self.ini_path}")
            return {}
        
        config = configparser.ConfigParser(
            interpolation=None,  # IMPORTANT: LinuxCNC INIs often contain % signs
            allow_no_value=True,
            inline_comment_prefixes=('#', ';')
        )
        config.optionxform = str  # Preserve case sensitivity
        
        try:
            config.read(self.ini_path)
            
            if section_name not in config.sections():
                logger.warning(f"Section [{section_name}] not found in INI")
                return {}
            
            params = {}
            for key, value in config[section_name].items():
                if value is None:
                    continue
                # Try to convert to number
                try:
                    params[key] = int(value)
                except ValueError:
                    try:
                        params[key] = float(value)
                    except ValueError:
                        params[key] = value
            
            return params
            
        except configparser.Error as e:
            logger.error(f"ConfigParser error reading INI: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading INI file: {e}")
            return {}
    
    def read_spindle_params(self) -> Dict[str, float]:
        """
        Read spindle parameters and map to tuning parameter names.
        
        Handles case-insensitive INI key matching.
        
        Returns:
            Dict with standardized parameter names
        """
        raw = self.read_section('SPINDLE_0')
        
        # Create case-insensitive lookup
        raw_lower = {k.upper(): v for k, v in raw.items()}
        
        # Map INI keys to parameter names
        mapping = {
            'P': 'P',
            'I': 'I', 
            'D': 'D',
            'FF0': 'FF0',
            'FF1': 'FF1',
            'DEADBAND': 'Deadband',
            'MAX_ERROR_I': 'MaxErrorI',
            'MAX_CMD_D': 'MaxCmdD',
            'RATE_LIMIT': 'RateLimit',
            'FILTER_GAIN': 'FilterGain',
        }
        
        params = {}
        for ini_key, param_name in mapping.items():
            if ini_key in raw_lower:
                try:
                    params[param_name] = float(raw_lower[ini_key])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {ini_key} in INI file")
        
        return params
    
    def generate_ini_section(self, params: Dict[str, float],
                            include_comments: bool = True) -> str:
        """
        Generate INI file section text.
        
        Args:
            params: Dict of parameter values
            include_comments: Include descriptive comments
            
        Returns:
            Formatted INI section text
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        lines = []

        def safe_value(key: str, default: float) -> float:
            try:
                return float(params.get(key, default))
            except (TypeError, ValueError):
                return default

        if include_comments:
            lines.extend([
                "# ==============================================================================",
                "# SPINDLE PID CONFIGURATION",
                f"# Generated by Spindle Tuner v6.0 on {timestamp}",
                "# Based on Spindle PID Tuning Guide v5.3",
                "# ==============================================================================",
                "",
            ])
        
        lines.append("[SPINDLE_0]")
        
        if include_comments:
            lines.append("# PID Gains")
        lines.extend([
            f"P = {safe_value('P', 0.1):.3f}",
            f"I = {safe_value('I', 1.0):.3f}",
            f"D = {safe_value('D', 0.0):.3f}",
            f"FF0 = {safe_value('FF0', 1.0):.3f}",
            f"FF1 = {safe_value('FF1', 0.35):.3f}",
            f"DEADBAND = {safe_value('Deadband', 10.0):.1f}",
            "",
        ])

        if include_comments:
            lines.append("# Anti-Windup Limits")
        lines.extend([
            f"MAX_ERROR_I = {safe_value('MaxErrorI', 60.0):.1f}",
            f"MAX_CMD_D = {safe_value('MaxCmdD', 1200.0):.1f}",
            "",
        ])

        if include_comments:
            lines.append("# Rate Limiting (match VFD accel time)")
        lines.extend([
            f"RATE_LIMIT = {safe_value('RateLimit', 1200.0):.1f}",
            "",
        ])

        if include_comments:
            lines.append("# Feedback Filter")
        lines.extend([
            f"FILTER_GAIN = {safe_value('FilterGain', 0.5):.2f}",
            "",
        ])
        
        if include_comments:
            lines.extend([
                "# Encoder Configuration",
                "ENCODER_SCALE = 4096",
                "VEL_TIMEOUT = 0.1",
                "",
                "# Speed Limits",
                "MIN_FORWARD_VELOCITY = 50",
                "MAX_FORWARD_VELOCITY = 1800",
                "AT_SPEED_TOLERANCE = 20",
                "",
                "# DPLL Configuration (for low-speed accuracy)",
                "DPLL_TIMER_US = -100",
            ])
        
        return '\n'.join(lines)
    
    def compare_with_baseline(self, params: Dict[str, float]) -> Dict[str, Tuple[float, float, str]]:
        """
        Compare parameters with baseline values.
        
        Args:
            params: Current parameter values
            
        Returns:
            Dict mapping param names to (current, baseline, status) tuples
            where status is 'same', 'higher', or 'lower'
        """
        comparison = {}

        for name, baseline in BASELINE_PARAMS.items():
            raw_value = params.get(name, baseline)
            try:
                current = float(raw_value)
            except (TypeError, ValueError):
                logger.warning(f"Non-numeric value for {name} in baseline comparison: {raw_value}")
                continue

            if abs(current - baseline) < 0.001:
                status = 'same'
            elif current > baseline:
                status = 'higher'
            else:
                status = 'lower'
            
            comparison[name] = (current, baseline, status)
        
        return comparison
