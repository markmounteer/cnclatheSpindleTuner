# Spindle PID Tuning Guide - Grizzly 7x14 CNC Lathe

**Version:** 5.3 — Enhanced with Motor Physics & Control Theory  
**Hardware:** Baldor M3558T motor, XSY-AT1 VFD, ABILKEEN 1024 PPR encoder, Mesa 7i76E  
**Control Topology:** Feedforward-Dominant with Integral Slip Compensation  
**Last Updated:** December 2024 (Safety hardening added 2025-12-05)

---

## Important Safety Notice

> **WARNING:** This guide involves tuning a high-power spindle system capable of causing serious injury. Always:
> - Wear appropriate protective equipment (safety glasses, no loose clothing)
> - Ensure E-stop is functional and within arm's reach
> - Test with no workpiece or tooling installed initially
> - Clear the work area of other personnel
> - Complete ALL safety verification steps (Sections 6.3, 6.6)
> - Remove commissioning bypasses before production use (Section 13)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview & Physics](#2-system-overview--physics)
3. [VFD Configuration](#3-vfd-configuration)
4. [Architecture & Signal Flow](#4-architecture--signal-flow)
5. [Pre-Flight Verification](#5-pre-flight-verification)
6. [Initial Startup Procedure](#6-initial-startup-procedure)
7. [Baseline Performance Testing](#7-baseline-performance-testing)
8. [Incremental Gain Tuning](#8-incremental-gain-tuning)
9. [Tuning by Symptom](#9-tuning-by-symptom)
10. [Threading & Synchronization](#10-threading--synchronization)
11. [Advanced Tuning Methods](#11-advanced-tuning-methods)
12. [Troubleshooting](#12-troubleshooting)
13. [Commissioning Cleanup](#13-commissioning-cleanup)
14. [Quick Reference & Decision Tree](#14-quick-reference--decision-tree)
15. [Appendix: Hardware Specifications](#15-appendix-hardware-specifications)

---

## 1. Executive Summary

### 1.1 System Characteristics at a Glance

| Component | Specification | Control Impact |
|-----------|---------------|----------------|
| **Motor** | Baldor M3558T, 2HP, 4-pole, 1750 RPM | 3-4% slip under load requires integrator action |
| **Inertia** | Rotor: 0.006 kg·m², System: ~0.028 kg·m² | Load dominates → FF1 = 0.35-0.4 for acceleration |
| **Thermal** | Slip: 2.7% (cold) → 3.6% (hot) over 20-30 min | PID must track 10-16 RPM thermal drift |
| **VFD** | XSY-AT1 scalar V/f, 1-2s transport delay | Limits P-gain to <0.3, requires rate limiting |
| **Encoder** | 1024 PPR (4096 counts/rev), differential | DPLL required for velocity accuracy below 100 RPM |

### 1.2 The "2DOF" Control Strategy

Unlike servo tuning where high P-gain dominates, VFD spindle control requires a **Two-Degree-of-Freedom (2DOF)** approach to overcome the VFD's inherent latency.

| Degree of Freedom | Components | Role | Contribution |
|-------------------|------------|------|--------------|
| **Tracking (Feedforward)** | FF0, FF1 | Predict voltage needed *before* error occurs | ~95% |
| **Rejection (Feedback)** | I (Integral) | Correct for slip and loads *after* error occurs | ~5% |

**Why P-gain is kept low:** The VFD takes ~1.5 seconds to reach commanded speed. Any P-gain > 0.3 causes oscillation because corrections arrive "too late."

**Why limit2 is critical:** Without rate limiting, step commands cause massive integrator windup during the 1.5s VFD ramp. The limit2 component matches command rate to VFD physics, eliminating this problem.

### 1.3 Critical Tuning Principles

1. **Feedforward Dominant:** FF0 (1.0) provides 95% of control signal; PID only corrects disturbances
2. **Rate Limiting Essential:** limit2.maxv = 1200 RPM/s prevents integrator windup
3. **Conservative P-Gain:** VFD latency limits P to 0.1-0.3; higher causes oscillation
4. **Integrator for Slip:** I = 1.0-1.5 accumulates correction for full-load slip
5. **Deadband Matches Reality:** DEADBAND = 10 RPM prevents hunting for unattainable precision

### 1.4 v5.3 Baseline Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **FF0** | 1.0 | Primary feedforward — direct RPM-to-voltage passthrough |
| **FF1** | 0.35 | Inertia compensation — based on J ≈ 0.028 kg·m² |
| **P** | 0.1 | Proportional — kept low due to 1.5s VFD delay |
| **I** | 1.0 | Integral — compensates for 50-65 RPM motor slip |
| **D** | 0 | Derivative — disabled (amplifies encoder noise) |
| **DEADBAND** | 10 | Hysteresis — matches natural slip fluctuation |
| **MAX_ERROR_I** | 60 | Anti-windup — covers hot-motor slip (~65 RPM) |
| **MAX_CMD_D** | 1200 | Spike limit — matches limit2 rate for FF1 protection |
| **limit2.maxv** | 1200 | Rate limit — matches VFD accel (1800 RPM / 1.5s) |

> **Tuning Tip:** These are physics-based starting points. Test incrementally using `halcmd setp` before committing to INI.

---

## 2. System Overview & Physics

### 2.1 Motor Behavior: Slip Under Load

**Slip Calculation:**
```
Slip (%) = (Synchronous RPM - Actual RPM) / Synchronous RPM × 100%
         = (1800 - 1750) / 1800 = 2.78% at rated load (cold)
```

**Load vs. Slip Table (Baldor M3558T):**

| Load % | Speed (RPM) | Slip % | PID Error (at 1000 RPM cmd) |
|--------|-------------|--------|----------------------------|
| 0% | ~1795 | 0.3% | -3 RPM |
| 50% | ~1777 | 1.3% | -13 RPM |
| 100% (cold) | ~1751 | 2.7% | -27 RPM |
| 100% (hot) | ~1741 | 3.3% | -33 RPM |
| 150% | ~1718 | 4.6% | -46 RPM |

**Thermal Effect:** Rotor resistance increases ~0.4%/°C for aluminum. From cold (25°C) to hot (80°C), slip increases from ~2.7% to ~3.6%, causing 10-16 RPM additional speed loss at full load.

**Why This Matters:** The I-term must accumulate enough correction to compensate for these slip variations. With I = 1.0 and a 30 RPM error, the integrator adds 30 RPM/s to the output, correcting in ~1-2 seconds.

### 2.2 Inertia & Acceleration Torque

**Total System Inertia:**
```
J_motor  = 0.006 kg·m²    (Baldor confirmed)
J_load   = ~0.022 kg·m²   (chuck + spindle estimated)
─────────────────────────────────────────────────────
J_total  ≈ 0.028 kg·m²
```

**Torque Required for 1000 RPM/s Acceleration:**
```
α = 1000 RPM/s = 104.7 rad/s²
τ_accel = J_total × α = 0.028 × 104.7 ≈ 2.93 N·m
τ_rated = 8.1 N·m (motor rated torque)
FF1 = τ_accel / τ_rated ≈ 0.36 → use 0.35-0.40
```

**Interpretation:** Accelerating at 1000 RPM/s requires ~36% of motor torque just for inertia. FF1 provides this instantly, preventing PID lag during ramps.

### 2.3 VFD Limitations & Transport Delay

The XSY-AT1 has significant cascaded delays:

| Component | Latency | Notes |
|-----------|---------|-------|
| Mesa servo thread | ~1 ms | Servo period |
| Analog output settling | ~10 ms | DAC + filtering |
| VFD signal processing | ~50-100 ms | Internal loop |
| **VFD frequency ramp** | **~1500 ms** | **Dominant constraint** |
| Motor flux buildup | ~100 ms | Electrical time constant |

**Control Theory Implication:** A 1-second delay causes 180° phase shift at 0.5 Hz. This fundamentally limits achievable bandwidth and necessitates low P-gain to avoid oscillation.

**Practical Result:** Any P-gain > 0.3 typically causes hunting because corrections arrive after the error has already reversed.

### 2.4 Encoder Velocity Accuracy

With 1024 PPR (4096 counts/rev) encoder:

| RPM | Counts/ms | Without DPLL | With DPLL |
|-----|-----------|--------------|-----------|
| 60 | 4 | ±25% | ±0.5% |
| 100 | 7 | ±15% | ±0.2% |
| 500 | 34 | ±3% | ±0.05% |
| 1800 | 123 | ±0.8% | ±0.01% |

**DPLL is critical below 100 RPM** for usable velocity feedback. Without it, low-speed velocity readings are too noisy for stable PID control.

### 2.5 Why This System is Challenging

- **Plant is Lag-Dominant:** VFD nonlinearities reduce usable gain below theoretical
- **Nonlinear Slip:** 3-5% load-dependent gain variation
- **Internal VFD Dynamics:** Unknown phase lag beyond measured dead time
- **Thermal Drift:** 10-16 RPM change over 20-30 minutes requires active tracking
- **Torque-Speed Coupling:** V/f control ties voltage to frequency; torque response requires flux buildup

---

## 3. VFD Configuration

> **WARNING:** Incorrect VFD settings can damage the motor, cause unstable behavior, or make PID tuning impossible. Configure the XSY-AT1 BEFORE connecting to LinuxCNC.

### 3.1 Critical Concept: VFD as "Dumb" Frequency Source

The VFD must act as a simple voltage-to-frequency converter. Internal "smart" features like torque boost and slip compensation often **fight** the LinuxCNC PID, causing oscillation or poor response.

### 3.2 Required XSY-AT1 Settings

| Parameter | Value | Purpose | Verification |
|-----------|-------|---------|--------------|
| P0.01 | 1 | Terminal control (FWD/REV pins) | Spindle runs with Mesa outputs |
| P0.03 | 1 | Analog input (0-10V) | Speed changes with voltage |
| P0.04 | **65** | Max frequency (headroom) | Motor can reach ~1950 RPM |
| P0.05 | **65** | Upper frequency limit | Matches P0.04 |
| P0.06 | 0 | Lower frequency limit | Allows full range |
| P0.11 | **1.5** | Acceleration time (1.0-2.0s) | Smooth ramps |
| P0.12 | **1.5** | Deceleration time | Matches accel |
| **P72** | **0** | **Torque boost DISABLED** | Preserves linear V/f |

### 3.3 Why These Settings?

**Acceleration Time (P0.11 = 1.5s):**
- Too slow (>3s): PID integrator winds up → overshoot
- Too fast (<0.5s): Motor trips on overcurrent
- Sweet spot (1-2s): VFD responds smoothly, PID can track
- This defines limit2 rate: `1800 RPM / 1.5s = 1200 RPM/s`

**Max Frequency (P0.04 = 65 Hz):**
- Base speed: 60 Hz → ~1750 RPM
- Slip compensation needs ~3% extra → 61.8 Hz
- Headroom for calibration → 65 Hz (108% of base)
- Motor can safely handle brief periods at 65 Hz

**Torque Boost (P72 = 0):**
- When enabled, VFD adds non-linear frequency boost at low speeds
- This fights the PID's linear control model
- Disabling ensures predictable response across all speeds

### 3.4 Optional: VFD Internal Slip Compensation

| Setting | Effect | Recommendation |
|---------|--------|----------------|
| 0% | PID handles all slip | **Recommended for learning** |
| 2-3% | VFD adds frequency under load | Reduces PID workload 60-80% |
| >3% | Risk of overcorrection | Start at 2%, increase if needed |

**If enabled:** Reduce PID I-gain proportionally (e.g., from 1.0 to 0.4-0.6).

### 3.5 VFD Manual Test (Before LinuxCNC)

1. Disconnect Mesa analog output from VFD
2. Apply 5V DC to VFD analog input (AI1)
3. Close FWD terminal to common
4. Motor should run at ~900 RPM (half speed)
5. Apply 10V → should run at ~1800 RPM
6. Verify smooth acceleration/deceleration

**If this fails:** VFD is misconfigured — PID tuning will fail.

---

## 4. Architecture & Signal Flow

### 4.1 v5.3 Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Grizzly7x14_Lathe.ini                                      │
│  ═══════════════════                                        │
│  SINGLE SOURCE OF TRUTH for all tuning parameters           │
│  FF0, FF1, P, I, D, DEADBAND, MAX_ERROR_I, MAX_CMD_D, etc.  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Grizzly7x14_Lathe.hal                                      │
│  ═════════════════════                                      │
│  Reads all [SPINDLE_0] parameters from INI                  │
│  Sets up hardware, signal chains, encoder watchdog          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  custom.hal                                                 │
│  ══════════                                                 │
│  ONLY contains:                                             │
│    - limit2 rate limiting (signal routing)                  │
│    - Commissioning bypass (temporary)                       │
│  NO parameter overrides                                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Signal Flow Diagrams

#### Command Path
```
┌────────────────────────────────────────────────────────────┐
│                      COMMAND PATH                          │
│                                                            │
│  [G-code S1000]                                            │
│        │                                                   │
│        ▼                                                   │
│  spindle.0.speed-out-abs (always positive)                 │
│        │                                                   │
│        ▼                                                   │
│  ┌─────────────┐                                           │
│  │   limit2    │◄── Rate limits to 1200 RPM/s              │
│  │             │    Prevents integrator windup             │
│  └─────────────┘    by matching VFD physics                │
│        │                                                   │
│        ▼                                                   │
│  pid.s.command (ramped, not stepped)                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### PID Calculation
```
┌────────────────────────────────────────────────────────────┐
│                    PID CALCULATION                         │
│                                                            │
│  pid.s.output = FF0×cmd + FF1×d(cmd)/dt + P×err + I×∫err   │
│                   │           │            │       │       │
│                   │           │            │       │       │
│        Base Voltage (95%)  Accel      Error    Slip       │
│        ≈ commanded RPM     Boost     Correct   Comp       │
│                                                            │
│  Example at S1000 with 30 RPM load droop:                  │
│    FF0 contribution: 1.0 × 1000 = 1000 RPM                 │
│    I contribution:   1.0 × 30 × time = +30 RPM/s           │
│    Total output:     ~1030 RPM (compensating slip)         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### Feedback Path
```
┌────────────────────────────────────────────────────────────┐
│                     FEEDBACK PATH                          │
│                                                            │
│  encoder.velocity (signed: + forward, - reverse)           │
│        │                                                   │
│        ▼                                                   │
│  RPS-to-RPM (×60)                                          │
│        │                                                   │
│        ▼                                                   │
│  lowpass filter (smoothing, gain=0.5)                      │
│        │                                                   │
│        ▼                                                   │
│  ABS component (always positive)◄── Handles M4 reverse     │
│        │                                                   │
│        ▼                                                   │
│  pid.s.feedback                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### Output and Direction Paths
```
┌────────────────────────────────────────────────────────────┐
│                      OUTPUT PATH                           │
│                                                            │
│  pid.s.output (0-1900 RPM range)                           │
│        │                                                   │
│        ▼                                                   │
│  spinout-scalemax (1800) ──► 0-10V analog                  │
│        │                                                   │
│        ▼                                                   │
│  VFD analog input ──► Motor                                │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    DIRECTION PATH                          │
│                                                            │
│  spindle.0.forward ──► VFD FWD terminal (M3)               │
│  spindle.0.reverse ──► VFD REV terminal (M4)               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Key v5.3 Features

| Feature | Purpose |
|---------|---------|
| **limit2 rate limiting** | Prevents integrator windup by ramping at VFD's physical rate |
| **maxcmdD** | Limits FF1 response to command derivative spikes |
| **vel-timeout = 0.1** | Faster zero-velocity detection when spindle stops |
| **INI as single source** | All tuning in one place, no custom.hal overrides |
| **Encoder watchdog** | Arms only when spindle enabled, prevents nuisance E-stop |
| **DPLL timing** | Accurate low-speed velocity measurement |

---

## 5. Pre-Flight Verification

### 5.1 Signal Chain Validation Script

Run with LinuxCNC loaded but machine power OFF:

```bash
# 1. Verify PID parameters from INI
echo "=== PID Parameters ==="
halcmd show pin pid.s.Pgain        # Expect: 0.1
halcmd show pin pid.s.Igain        # Expect: 1.0
halcmd show pin pid.s.FF0          # Expect: 1.0
halcmd show pin pid.s.FF1          # Expect: 0.35
halcmd show pin pid.s.maxerrorI    # Expect: 60
halcmd show pin pid.s.maxcmdD      # Expect: 1200

# 2. Verify v5.3 enhancements
echo "=== v5.3 Features ==="
halcmd show pin spindle-cmd-limit.maxv              # Expect: 1200
halcmd show pin hm2_7i76e.0.encoder.00.vel-timeout  # Expect: 0.1
halcmd show param hm2_7i76e.0.dpll.01.timer-us      # Expect: -100
halcmd show pin hm2_7i76e.0.encoder.timer-number    # Expect: 1

# 3. Verify safety chain
echo "=== Safety Chain ==="
halcmd show sig encoder-fault              # Expect: FALSE
halcmd show sig encoder-watchdog-is-armed  # Expect: FALSE (spindle off)
halcmd show sig external-ok                # Expect: TRUE
```

### 5.2 Encoder Direction Test (Hand-Spin)

```bash
# Spin spindle FORWARD (M3 direction):
halcmd show sig spindle-vel-fb-rpm      # Should be POSITIVE

# Spin spindle REVERSE (M4 direction):
halcmd show sig spindle-vel-fb-rpm      # Should be NEGATIVE

# ABS signal (always positive):
halcmd show sig spindle-vel-fb-rpm-abs  # Should ALWAYS be ≥0
```

> **CRITICAL:** If `spindle-vel-fb-rpm` is negative when spinning forward, the PID will run away to maximum speed! Fix encoder wiring or invert ENCODER_SCALE in INI.

### 5.3 Hardware Verification Checklist

| Item | Check | Pass Criteria |
|------|-------|---------------|
| Encoder jumpers | W10, W11, W13 position | RIGHT position (differential mode) |
| Shield grounding | Shield connection | Connected at Mesa end ONLY |
| Cable separation | Distance from VFD cables | ≥6" (15cm) minimum |
| VFD analog input | Multimeter test | 0V=0 RPM, 10V=1800 RPM |
| Mesa 7i76E LEDs | Visual check | Green solid, red blinking |
| E-stop | Function test | Cuts all power when pressed |

### 5.4 DPLL Verification

```bash
# Check DPLL configuration
halcmd show param hm2_7i76e.0.dpll.01.timer-us      # Should be -100
halcmd show pin hm2_7i76e.0.encoder.timer-number    # Should be 1

# Monitor phase error (should be stable)
watch -n 0.5 "halcmd show param hm2_7i76e.0.dpll.phase-error-us"
# Should be ±50 µs, not cycling wildly
```

**If DPLL not configured:** Velocity readings below 100 RPM will be unusably noisy.

---

## 6. Initial Startup Procedure

> **Safety First:** Clear the work area, keep hand on E-stop, start with no tool or workpiece.

### 6.1 Step 1: Open-Loop Baseline Test

Temporarily disable PID feedback to verify basic VFD operation:

```bash
halcmd setp pid.s.Pgain 0
halcmd setp pid.s.Igain 0
halcmd setp pid.s.FF0 1.0
```

Command: `M3 S1000`

**Verify:**
- `halcmd show pin pid.s.output` should be ~1000
- Actual RPM should be ~950-980 (2-3% slip is normal)

**If way off:** VFD_SCALE is wrong, or VFD P0.03/P0.04 misconfigured.

### 6.2 Step 2: Restore PID and Test Forward (M3)

```bash
halcmd setp pid.s.Pgain 0.1
halcmd setp pid.s.Igain 1.0
```

Command: `M3 S500`

**Watch for:**
- Smooth acceleration (ramped by limit2, not stepped)
- Settles to ~500 RPM within a few seconds
- `spindle-is-at-speed` goes TRUE
- No oscillation or hunting

### 6.3 Step 3: Test Reverse (M4) — CRITICAL SAFETY TEST

Command: `M5` (stop first)  
Command: `M4 S500`

> **WATCH FOR RUNAWAY!** Be ready to hit E-stop immediately.

**Correct behavior:**
- Spindle runs reverse at ~500 RPM
- `halcmd show sig spindle-vel-fb-rpm` shows NEGATIVE (~-500)
- `halcmd show sig spindle-vel-fb-rpm-abs` shows POSITIVE (~500)
- Speed stays at commanded value, NO acceleration beyond

**If runaway occurs:** ABS component is broken or miswired — **EMERGENCY STOP!**

### 6.4 Step 4: Verify limit2 Operation

```bash
halcmd show sig spindle-vel-cmd-rpm-raw      # Raw command
halcmd show sig spindle-vel-cmd-rpm-limited  # Rate-limited
```

Command: `M3 S1500`

- Raw signal should step to 1500 immediately
- Limited signal should ramp at 1200 RPM/s (takes ~1.25 seconds)

**If both step instantly:** limit2 is not connected — check custom.hal

### 6.5 Step 5: Load Test

With spindle at `M3 S500`:
- Apply light friction (wood against chuck — **NOT your hand!**)
- Watch RPM droop momentarily
- Should recover to ~500 within 1-3 seconds

**If no recovery:** I-gain too low, or maxerrorI limiting integrator.

### 6.6 Step 6: Encoder Watchdog Test — DO NOT SKIP

> **This test verifies your safety system works. Skipping it is dangerous.**

With spindle running at `M3 S500`:
1. Carefully disconnect encoder cable
2. Machine should E-stop within ~1 second
3. **If no E-stop:** SAFETY SYSTEM IS BROKEN — DO NOT OPERATE!

Reconnect encoder, reset E-stop, verify normal operation resumes.

---

## 7. Baseline Performance Testing

Before tuning, establish baseline metrics to measure improvement.

### 7.1 Test A: Speed Step Response

```
In MDI:
  M3 S500
  (wait for at-speed TRUE)
  S1200
```

**Measure:**
- Settling time (to within ±20 RPM of target)
- Overshoot (peak RPM above 1200)
- Command following error during ramp

### 7.2 Test B: Load Recovery

```
M3 S1000
Apply light friction with wood
Release
```

**Measure:**
- Maximum RPM droop under load
- Time to recover to within ±20 RPM

### 7.3 Test C: Steady-State Accuracy

```
M3 S1000
Wait 30 seconds for thermal stabilization
halcmd show pin pid.s.error
halcmd show pin pid.s.errorI
```

### 7.4 Performance Targets

| Metric | Good | Excellent | Notes |
|--------|------|-----------|-------|
| Step settle time | 2-3s | 1.5-2s | To within ±20 RPM |
| Overshoot | <10% | <5% | With limit2 active |
| Load recovery | 2-3s | 1-2s | Back to ±20 RPM |
| Steady-state error | ±15 RPM | ±8 RPM | At constant load |
| Thermal tracking | Yes | <5 RPM error | Over 30 min operation |

### 7.5 Recording Template

```
Date: __________
Config Version: v5.3
VFD Settings: P0.04=___, P0.11=___, P72=___, Slip Comp=___%

1. Step Response (S500 → S1200):
   - Settle time: ______ s
   - Overshoot: ______ RPM (______ %)
   - Ramp tracking error: max ______ RPM

2. Load Test (wood friction at S1000):
   - Max droop: ______ RPM
   - Recovery time: ______ s
   - Final error: ______ RPM

3. Steady-State (S1000, 30s):
   - pid.s.error: ______ RPM
   - pid.s.errorI: ______ (limit: 60)
   - Variation (min/max): ______/______ RPM

Notes: ______________________________________
```

---

## 8. Incremental Gain Tuning

### 8.1 Tuning Philosophy: Feedforward First

**Priority Order:**
1. **FF0** — Establish correct open-loop scaling (already 1.0)
2. **FF1** — Optimize acceleration tracking (target 0.35-0.4)
3. **I** — Tune load rejection (target 1.0-1.5)
4. **P** — Fine-tune disturbance response (keep ≤0.3)
5. **Deadband** — Eliminate hunting (10-20 RPM)

> **Golden Rule:** Change ONE parameter at a time, test, then decide.

### 8.2 Tuning Workflow

1. Test parameter change with `halcmd setp`
2. Run performance tests (Section 7)
3. **If improvement:** Update INI file
4. **If degradation:** Revert with `halcmd setp`
5. Restart LinuxCNC to confirm INI changes

### 8.3 FF1 Tuning: Acceleration Feedforward

**Current:** 0.35  
**Target range:** 0.35-0.45 based on actual inertia

```bash
halcmd setp pid.s.FF1 0.40
```

Test: `M3 S500`, wait, then `S1500`

**Better:** Reduced lag during acceleration, error < 50 RPM throughout ramp  
**Worse:** Increased overshoot at target, oscillation after settling

**Physics check:** If your chuck is heavier than standard, FF1 may need 0.4-0.45.

### 8.4 I-Gain Tuning: Slip Compensation

**Current:** 1.0  
**Target range:** 0.8-1.5 depending on VFD slip compensation

```bash
halcmd setp pid.s.Igain 1.2
```

Test: Apply and release load at `M3 S1000`

**Monitor integrator:**
```bash
watch -n 0.2 "halcmd show pin pid.s.errorI"
```

**Better:** Faster recovery, error returns to <10 RPM within 2 seconds  
**Worse:** Oscillation after load release, errorI hitting max limit

**If errorI hits 60:** Either increase maxerrorI OR reduce I-gain.

### 8.5 P-Gain Tuning: Disturbance Response

**Current:** 0.1  
**Maximum safe:** 0.3 (VFD latency limited)

```bash
halcmd setp pid.s.Pgain 0.15
```

Test small speed step: `M3 S1000`, then `S1100`

**Better:** Smaller steady-state error, faster minor corrections  
**Worse:** Sustained oscillation, hunting around setpoint

> **VFD Reality:** Most XSY-AT1 systems cannot tolerate P > 0.2-0.25.

### 8.6 Parameter Interdependencies

When adjusting one parameter, consider its interactions:

| Change | May Require | Reason |
|--------|-------------|--------|
| Increase I-gain | Increase maxerrorI | Prevent integrator saturation |
| Increase FF1 | May reduce I | FF1 reduces acceleration error burden |
| Increase P | May reduce I | P and I both respond to error |
| Enable VFD slip comp | Reduce I by 40-60% | VFD handles some compensation |

### 8.7 Common Parameter Ranges

| Parameter | Minimum | Typical | Maximum | Notes |
|-----------|---------|---------|---------|-------|
| P | 0.05 | 0.1-0.15 | 0.3 | >0.3 usually oscillates |
| I | 0.5 | 1.0-1.2 | 2.0 | Higher = faster recovery |
| FF1 | 0.2 | 0.35-0.4 | 0.5 | Based on inertia |
| DEADBAND | 5 | 10-15 | 25 | Larger = stable but less precise |
| maxerrorI | 30 | 60-80 | 100 | Must allow full slip comp |
| limit2.maxv | 600 | 1200 | 2000 | Match VFD acceleration |

---

## 9. Tuning by Symptom

### 9.1 Oscillation/Hunting at Steady State

**Symptoms:** RPM cycles ±5-15 RPM continuously, at-speed flickers

**Fixes (try in order):**
```bash
# 1. Reduce P-gain (most likely cause)
halcmd setp pid.s.Pgain 0.05

# 2. Increase deadband
halcmd setp pid.s.deadband 15

# 3. Check limit2 is working
halcmd show sig spindle-vel-cmd-rpm-limited

# 4. Reduce I-gain (if slow oscillation, >2s period)
halcmd setp pid.s.Igain 0.8
```

### 9.2 Slow Oscillation (Period > 3 seconds)

**Cause:** VFD internal features fighting LinuxCNC PID

**Fix:** Disable VFD torque boost and slip compensation:
- Set VFD P72 = 0 (torque boost off)
- Disable any VFD slip compensation parameters

### 9.3 Overshoot on Speed Changes

**Symptoms:** Speed exceeds target by 5-15%, then settles back

```bash
# 1. Verify limit2 is active
halcmd show pin spindle-cmd-limit.maxv  # Should be 1200

# 2. Reduce FF1 (if overshoot immediate)
halcmd setp pid.s.FF1 0.25

# 3. Reduce I-gain (if overshoot develops slowly)
halcmd setp pid.s.Igain 0.8
```

With limit2 working, overshoot should be <5%. If significant, limit2 may not be connected.

### 9.4 Slow Load Recovery

**Symptoms:** RPM droops under load, takes >3s to recover

```bash
# 1. Increase I-gain (primary fix)
halcmd setp pid.s.Igain 1.2

# 2. Check integrator not saturating
halcmd show pin pid.s.errorI
# If near maxerrorI (60), increase limit:
halcmd setp pid.s.maxerrorI 80

# 3. Small increase in P (if stable)
halcmd setp pid.s.Pgain 0.15
```

### 9.5 Speed Never Reaches Target

**Symptoms:** Actual RPM consistently 3-10% below commanded

```bash
# 1. Check open-loop scaling
halcmd setp pid.s.Pgain 0
halcmd setp pid.s.Igain 0
M3 S1000
# Should be ~970-980 (2-3% slip)

# 2. Check PID output saturation
halcmd show pin pid.s.output
# At S1000, should be ~1030-1040 (compensating slip)

# 3. Check maxerrorI not too low
halcmd setp pid.s.maxerrorI 80

# 4. Check VFD max frequency
# P0.04 must be ≥62 Hz for full slip compensation
```

### 9.6 Thermal Drift Not Corrected

**Symptoms:** Speed gradually decreases 10-20 RPM over 20-30 minutes

This is NORMAL for induction motors. PID should track it:

```bash
# Monitor integrator during warm-up
watch -n 10 "halcmd show pin pid.s.errorI"

# Should gradually increase as motor heats
# If not increasing, I-gain too low:
halcmd setp pid.s.Igain 1.2

# If hits maxerrorI and stops tracking:
halcmd setp pid.s.maxerrorI 80
```

### 9.7 Reverse (M4) Runaway

> **CRITICAL SAFETY ISSUE — STOP IMMEDIATELY**

**Cause:** ABS component missing or miswired

```bash
# Check ABS signal
halcmd show sig spindle-vel-fb-rpm-abs
# MUST always be positive, even when spindle-vel-fb-rpm is negative
```

If negative values appear, fix feedback path before operating.

---

## 10. Threading & Synchronization

### 10.1 How Threading Really Works

**Critical understanding:** Thread pitch accuracy depends on **position synchronization**, NOT speed control.

```
Z_position = Z_start + (spindle_revs - spindle_revs_start) × pitch
```

**Implication:** Even if spindle speed varies ±10%, Z-axis slows proportionally, maintaining correct pitch.

**What closed-loop spindle provides:**
- Consistent acceleration profiles → predictable Z-axis behavior
- Reduced speed variation → less following error on Z-axis
- Better multi-pass alignment → threads start at same point

### 10.2 Threading-Specific Settings

**At-speed tolerance:**
```ini
[SPINDLE_0]
AT_SPEED_TOLERANCE = 20  # RPM
```

Adjust if threading won't start (waits forever for at-speed):
- Increase to 30-40 RPM if speed fluctuates
- But first fix underlying oscillation if present

**Index pulse verification:**
```bash
halmeter pin spindle.0.revs
# Should increment +1.000 each revolution
# Check for missing counts or direction errors
```

### 10.3 G76 Multi-Pass Threading Optimization

For best results:
- **Consistent acceleration:** FF1 ensures same torque profile each pass
- **Minimal speed droop:** PID maintains speed during cut
- **Stable at-speed:** Threading starts at consistent point

Test with simple thread:
```gcode
G76 X... Z... I... K... D... A... P...
```

Monitor: Each pass should start at same rotational position.

### 10.4 Threading Issues & Solutions

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| Threading won't start | at-speed never TRUE | Increase AT_SPEED_TOLERANCE to 30 |
| Thread pitch varies | Encoder counts missed | Check wiring, set filter=1 |
| Tool marks not aligned | Speed varies between passes | Reduce P, increase deadband |
| Z-axis lags/stalls | Spindle decelerates under load | Increase I-gain |
| Following error | Z can't track speed changes | Reduce max spindle accel (FF1) |

---

## 11. Advanced Tuning Methods

### 11.1 Relay Auto-Tune

LinuxCNC's PID has built-in auto-tuning:

```bash
M3 S1000  # Start at mid-range, wait for stable

halcmd setp pid.s.tune-mode 1        # Enable auto-tune
halcmd setp pid.s.tune-type 1        # P/I/FF1 mode
halcmd setp pid.s.tune-cycles 50     # Characterization cycles
halcmd setp pid.s.tune-effort 100    # Relay amplitude (RPM)

halcmd setp pid.s.tune-start 1       # Begin

# Wait for completion, then read results:
halcmd show pin pid.s.ultimate-gain
halcmd show pin pid.s.ultimate-period
halcmd show pin pid.s.Pgain          # Computed value
halcmd show pin pid.s.Igain          # Computed value

halcmd setp pid.s.tune-mode 0        # Disable
```

> **Caution:** Auto-tune often suggests P-gains too high for VFDs (0.5-2.0). Use as starting point, then **reduce P by 50-70%**.

### 11.2 Manual Ziegler-Nichols

**Step 1:** Start with minimal gains
```bash
halcmd setp pid.s.Pgain 0.05
halcmd setp pid.s.Igain 0
halcmd setp pid.s.FF1 0
```

**Step 2:** Find Ultimate Gain (Ku)

With spindle at M3 S1000:
- Gradually increase P: 0.10, 0.15, 0.20, 0.25, 0.30...
- Apply light load between changes
- Watch for sustained oscillation (±20 RPM hunting)

Record:
- Ku = P value at oscillation onset
- Tu = oscillation period in seconds

**Step 3:** Calculate gains
```
P = 0.6 × Ku
I = 2 × P / Tu
```

**Step 4:** Apply with VFD safety factor
```bash
# Use 50% of calculated P for VFD systems
halcmd setp pid.s.Pgain [calculated × 0.5]
halcmd setp pid.s.Igain [calculated]
```

### 11.3 Model-Based Tuning (SIMC/IMC)

**Plant model for Baldor M3558T + XSY-AT1:**
- Dead time τd: 0.1-0.2s (VFD processing)
- Time constant τ: 1.0-2.0s (VFD ramp + motor)
- Gain K: ~1.0 (normalized)

**SIMC calculation:**
```
τc = max(0.1τ, τd) ≈ 0.15s
Kp = (1/K) × (τ/(τc+τd)) = 1 × (1.5/0.3) = 5.0
Ti = min(τ, 4(τc+τd)) = 1.2s
Ki = Kp/Ti = 4.17
```

**Reality check:** Theoretical Kp=5.0, but practical max is 0.3. This 17× discrepancy is due to VFD nonlinearities not captured in linear models.

---

## 12. Troubleshooting

### 12.1 LinuxCNC Startup Issues

**"Unexpected realtime delay":**
```bash
latency-histogram --nobase --show --duration 10
```
Solutions: PREEMPT-RT kernel, disable CPU scaling, light GUI

**"Signal already linked":**
```bash
halcmd show sig  # Find conflicting connections
```
Fix: Remove duplicates in custom.hal

### 12.2 Encoder Problems

**No counts:**
- Check differential jumpers (W10, W11, W13 = RIGHT)
- Verify 5V power to encoder
- Test with filter=0 temporarily

**Velocity reads zero but position changes:**
```bash
# DPLL not configured
setp hm2_7i76e.0.encoder.00.timer-number 1
setp hm2_7i76e.0.dpll.01.timer-us -100
```

### 12.3 VFD Communication Issues

**Analog output stuck:**
```bash
halcmd show pin hm2_7i76e.0.7i76.0.0.spinout
halcmd show param hm2_7i76e.0.7i76.0.0.spinout-scalemax  # Should be 1800
```

**VFD faults on start:**
- Check motor connections
- Increase P0.11 (acceleration time) to 2.0-3.0
- Reduce FF1

### 12.4 PID Behavioral Issues

**Integrator windup then overshoot:**
```bash
# Check limit2
halcmd show sig spindle-vel-cmd-rpm-limited
# Reduce maxerrorI
halcmd setp pid.s.maxerrorI 50
```

**Oscillation at specific RPM only:**
- Likely VFD torque boost nonlinearity
- Set P72=0 in VFD

### 12.5 Emergency Procedures

**Runaway spindle:**
1. HIT PHYSICAL E-STOP
2. Disconnect VFD power
3. Check ABS component
4. Verify encoder direction

**Encoder failure during operation:**
- Machine should E-stop automatically (watchdog)
- If not, manual E-stop
- Verify watchdog logic before restarting

---

## 13. Commissioning Cleanup

> **Required for Safe Operation:** Complete before production use.

### 13.1 Enable Soft Limits

In `Grizzly7x14_Lathe.ini`:
```ini
[JOINT_0]  # X-axis
MIN_LIMIT = -0.5
MAX_LIMIT = 85.0    # Your actual travel minus margin

[JOINT_1]  # Z-axis
MIN_LIMIT = -2.0
MAX_LIMIT = 280.0   # Your actual travel minus margin
```

**Procedure:**
1. Home machine
2. Jog to physical limits
3. Note positions, subtract 2-5mm margin
4. Update INI and restart

### 13.2 Remove Drives-OK Bypass

In `custom.hal`, **DELETE**:
```hal
unlinkp drives-ok.in0
unlinkp drives-ok.in1
setp drives-ok.in0 1
setp drives-ok.in1 1
```

**Before removal, verify:**
1. VFD alarm output wired to Mesa Input-03
2. Servo alarm output wired to Mesa Input-04
3. Test: Force faults → E-stop triggers

### 13.3 Safety Validation

- [ ] Soft limits prevent crashes at travel extremes
- [ ] E-stop cuts all motion and spindle
- [ ] Encoder watchdog triggers on encoder disconnect
- [ ] VFD fault triggers E-stop
- [ ] Servo fault triggers E-stop

### 13.4 Safety Hardening Recommendations

**Gate Spindle Enable with E-stop Chain:**

For defense-in-depth, gate the spindle enable signal with the E-stop chain so the VFD run signal cannot remain asserted if `external-ok` drops:

```hal
# Example: Gate spindle-on with external-ok
# In custom.hal or main HAL file:
loadrt and2 names=spindle-estop-gate
addf spindle-estop-gate servo-thread

net spindle-on-request spindle.0.on => spindle-estop-gate.in0
net external-ok => spindle-estop-gate.in1
net spindle-on-gated spindle-estop-gate.out => [VFD enable output]
```

This ensures:
- VFD cannot receive run command if E-stop chain is broken
- Provides redundancy beyond motion controller's internal checks
- Protects against software faults that might leave spindle running

**Speed Filter Reset (Optional):**

Consider resetting the velocity lowpass filter when the spindle is disabled to prevent stale filtered values from affecting the next startup:

```hal
# Optional: Reset lowpass filter on spindle disable
# Ensures clean velocity reading on next enable
net spindle-on => lowpass.0.load  # Load input clears filter
```

This prevents the filter from holding old values that could:
- Cause momentary at-speed false positives
- Affect initial PID response on restart

> **Note:** Test filter reset behavior carefully. Some configurations may prefer the filter to retain its last value for faster settling on restart.

### 13.5 Documentation & Backup

```bash
# Save tuned configuration
cp Grizzly7x14_Lathe.ini Grizzly7x14_Lathe_v5.3_tuned.ini
cp custom.hal custom_v5.3_tuned.hal
```

Record final settings:
```
Final Configuration: v5.3 tuned
Date: __________

Motor: Baldor M3558T
VFD: XSY-AT1 (P0.04=___, P0.11=___, P72=___)

PID Gains:
  FF0=1.0, FF1=_____, P=_____, I=_____, D=0
  DEADBAND=_____, MAX_ERROR_I=_____

Performance:
  Step settle: _____ s, Overshoot: _____%
  Load recovery: _____ s
  Steady-state error: ±_____ RPM
```

---

## 14. Quick Reference & Decision Tree

### 14.1 v5.3 Baseline Parameters

```ini
[SPINDLE_0]
VFD_SCALE = 1800
PID_MAX_OUTPUT = 1900

FF0 = 1.0
FF1 = 0.35
P = 0.1
I = 1.0
D = 0
DEADBAND = 10

MAX_ERROR_I = 60
MAX_CMD_D = 1200
RATE_LIMIT = 1200

ENCODER_SCALE = 4096
VEL_TIMEOUT = 0.1
AT_SPEED_TOLERANCE = 20
```

### 14.2 Halcmd Quick Reference

```bash
# Temporary tuning
halcmd setp pid.s.FF1 0.4
halcmd setp pid.s.Igain 1.2
halcmd setp pid.s.maxerrorI 80

# Monitoring
halcmd show pin pid.s.error
halcmd show pin pid.s.errorI
halcmd show sig spindle-vel-cmd-rpm-limited

# Safety checks
halcmd show sig encoder-fault
halcmd show sig external-ok
```

### 14.3 Pre-Flight Checklist

- [ ] PID params match baseline (`halcmd show pin pid.s.FF1` = 0.35)
- [ ] limit2 enabled (`spindle-cmd-limit.maxv` = 1200)
- [ ] Encoder polarity correct (positive when spinning forward)
- [ ] ABS always positive (`spindle-vel-fb-rpm-abs` ≥ 0)
- [ ] DPLL configured (`encoder.timer-number` = 1)
- [ ] Encoder fault OK (`encoder-fault` = FALSE)
- [ ] Safety chain active (`external-ok` = TRUE)

### 14.4 Tuning Decision Tree

```
Spindle unstable/oscillating?
├─ Fast oscillation → Reduce P (0.1→0.05), increase DEADBAND
├─ Slow oscillation → Disable VFD torque boost (P72=0)
└─ No → Speed not reaching target?
         ├─ Yes → Check: VFD scaling, maxerrorI, VFD P0.04≥62Hz
         └─ No → Load causes large droop?
                 ├─ Yes → Increase I (1.0→1.2), ensure maxerrorI>60
                 └─ No → Overshoot on speed changes?
                         ├─ Yes → Check limit2 working, reduce FF1
                         └─ No → TUNING COMPLETE ✓
```

### 14.5 Upgrade Path

| Current | If Stable | Next Test |
|---------|-----------|-----------|
| FF1=0.35 | Ramp tracking good | Try FF1=0.40 |
| I=1.0 | Load recovery OK | Try I=1.2 |
| I=1.2 | Still stable | Try I=1.5 + maxerrorI=80 |
| maxerrorI=60 | errorI never saturates | Leave as-is |
| maxerrorI=60 | errorI hits limit | Increase to 80 |

---

## 15. Appendix: Hardware Specifications

### 15.1 Baldor M3558T Motor

| Parameter | Value | Units | Notes |
|-----------|-------|-------|-------|
| Power | 2 | HP | Derate to 1.0 SF for VFD |
| Voltage | 208-230/460 | V | Using 230V config |
| Full Load Amps | 6.2 | A | @ 230V |
| Synchronous Speed | 1800 | RPM | @ 60 Hz, 4-pole |
| Nameplate Speed | 1750 | RPM | Full load, cold |
| Full Load Torque | 8.1 | N·m | 6.0 lb·ft |
| Rotor Inertia | 0.00598 | kg·m² | 0.142 lb·ft² |
| Cold Slip | 2.7 | % | ~50 RPM @ 1800 |
| Hot Slip | 3.6 | % | ~65 RPM @ 1800 |
| Thermal Time Constant | 20-30 | min | To 63% of final temp |

### 15.2 ABILKEEN Encoder

| Parameter | Value | Notes |
|-----------|-------|-------|
| PPR | 1024 | 4096 counts/rev with quadrature |
| Output | Differential RS-422 | A+/A-, B+/B-, Z+/Z- |
| Supply | 5V DC | From Mesa 7i76E |
| Max Frequency | >500 kHz | Far exceeds 1800 RPM requirement |
| Index | Once per revolution | For threading synchronization |

**Mesa Configuration:**
```hal
setp hm2_7i76e.0.encoder.00.scale 4096
setp hm2_7i76e.0.encoder.00.filter 1
setp hm2_7i76e.0.encoder.00.counter-mode 0
setp hm2_7i76e.0.encoder.00.timer-number 1
setp hm2_7i76e.0.encoder.00.vel-timeout 0.1
setp hm2_7i76e.0.dpll.01.timer-us -100
```

### 15.3 XSY-AT1 VFD Final Settings

| Parameter | Value | Function |
|-----------|-------|----------|
| P0.01 | 1 | Terminal control |
| P0.03 | 1 | Analog input (0-10V) |
| P0.04 | 65 | Maximum frequency |
| P0.05 | 65 | Upper frequency limit |
| P0.06 | 0 | Lower frequency limit |
| P0.11 | 1.5 | Acceleration time |
| P0.12 | 1.5 | Deceleration time |
| P72 | 0 | Torque boost DISABLED |

### 15.4 Mesa 7i76E Connections

| Function | Terminal | Signal |
|----------|----------|--------|
| Spindle analog | TB3 AOUT0 | 0-10V to VFD |
| Spindle enable | TB3 OUT0 | VFD FWD terminal |
| Spindle direction | TB3 OUT1 | VFD REV terminal |
| Encoder A+ | TB4 ENC0A+ | Differential A |
| Encoder B+ | TB4 ENC0B+ | Differential B |
| Encoder Z+ | TB4 ENC0Z+ | Index pulse |
| VFD fault | TB6 IN03 | NC contact |
| E-stop | TB6 IN05 | NC contact |

---

*Spindle PID Tuning Guide v5.3 — December 2024*  
*For Grizzly 7x14 CNC Lathe with Baldor M3558T & XSY-AT1 VFD*
