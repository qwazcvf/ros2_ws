"""
Unit tests for safety_manager.py.
"""

import time
import pytest
from nano_base_bridge.safety_manager import SafetyManager
from nano_base_bridge.protocol import BaseCommand, BaseFeedback

DEFAULT_PARAMS = {
    "max_speed_mps": 0.10,
    "max_reverse_speed_mps": 0.05,
    "max_steering_angle_rad": 0.35,
    "cmd_vel_timeout_sec": 0.5,
    "hardware_feedback_timeout_sec": 0.5,
    "communication_timeout_sec": 0.5,
    "send_stop_on_startup": True,
    "send_stop_on_shutdown": True,
    "stop_on_estop": True,
    "simulation_mode": True,
}


def _manager(**overrides):
    p = dict(DEFAULT_PARAMS)
    p.update(overrides)
    return SafetyManager(p)


def _fb(**overrides):
    f = {
        "speed_mps": 0.0,
        "steering_angle_rad": 0.0,
        "battery_voltage": 24.0,
        "battery_percentage": 100.0,
        "estop_active": False,
        "error_code": 0,
        "error_text": "",
        "connected": True,
        "stamp_sec": time.time(),
    }
    f.update(overrides)
    return BaseFeedback(**f)


def _cmd(**overrides):
    c = {
        "speed_mps": 0.08,
        "steering_angle_rad": 0.0,
        "motion_mode": "FORWARD",
        "stamp_sec": time.time(),
        "safe_stop": False,
        "stop_reason": "",
    }
    c.update(overrides)
    return BaseCommand(**c)


# ------------------------------------------------------------------
#  Startup STOP
# ------------------------------------------------------------------

def test_startup_stop():
    mgr = _manager(simulation_mode=True)
    raw = _cmd()
    fb = _fb()
    now = time.time()
    safe, state = mgr.evaluate(raw, now - 0.1, now, fb, True)
    assert safe.motion_mode == "STOP"
    assert safe.safe_stop is True
    assert state.last_stop_reason == "startup"


# ------------------------------------------------------------------
#  Normal forward (simulation mode)
# ------------------------------------------------------------------

def test_normal_forward_simulation():
    mgr = _manager(simulation_mode=True)
    # First call triggers startup STOP
    raw = _cmd()
    fb = _fb()
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup

    # Second call should pass through
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 0.1, now2, fb, True)
    assert safe.motion_mode == "FORWARD"
    assert safe.safe_stop is False
    assert state.last_stop_reason == ""


# ------------------------------------------------------------------
#  cmd_vel timeout → STOP
# ------------------------------------------------------------------

def test_cmd_vel_timeout_stop():
    mgr = _manager(simulation_mode=True)
    raw = _cmd()
    fb = _fb()
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup

    # Second call with stale cmd_vel time (>0.5s ago)
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 1.0, now2, fb, True)
    assert safe.motion_mode == "STOP"
    assert state.last_stop_reason == "cmd_vel_timeout"


# ------------------------------------------------------------------
#  Speed limit enforcement
# ------------------------------------------------------------------

def test_speed_limit():
    mgr = _manager(simulation_mode=True)
    raw = _cmd(speed_mps=2.0, motion_mode="FORWARD")
    fb = _fb()
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 0.1, now2, fb, True)
    assert safe.speed_mps <= 0.10


# ------------------------------------------------------------------
#  Reverse speed limit
# ------------------------------------------------------------------

def test_reverse_speed_limit():
    mgr = _manager(simulation_mode=True)
    raw = _cmd(speed_mps=-2.0, motion_mode="BACKWARD")
    fb = _fb()
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 0.1, now2, fb, True)
    assert safe.speed_mps >= -0.05


# ------------------------------------------------------------------
#  Steering limit enforcement
# ------------------------------------------------------------------

def test_steering_limit():
    mgr = _manager(simulation_mode=True)
    raw = _cmd(steering_angle_rad=1.0, motion_mode="LEFT")
    fb = _fb()
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now - 0.1, now, fb, True)
    assert abs(safe.steering_angle_rad) <= 0.35


# ------------------------------------------------------------------
#  e-stop active → STOP
# ------------------------------------------------------------------

def test_estop_stop():
    mgr = _manager(simulation_mode=True)
    raw = _cmd()
    fb = _fb()
    now = time.time()
    # Consume startup STOP first
    mgr.evaluate(raw, now - 0.1, now, fb, True)
    # Now test e-stop with fresh manager state (bypassing startup)
    # Create a new manager with send_stop_on_startup=False to test estop directly
    mgr2 = _manager(simulation_mode=True, send_stop_on_startup=False)
    fb_estop = _fb(estop_active=True)
    now2 = time.time()
    safe, state = mgr2.evaluate(raw, now2 - 0.1, now2, fb_estop, True)
    assert safe.motion_mode == "STOP"
    assert state.last_stop_reason == "estop_active"


# ------------------------------------------------------------------
#  Hardware mode: no connection → STOP
# ------------------------------------------------------------------

def test_hardware_mode_no_connection_stop():
    mgr = _manager(simulation_mode=False)
    raw = _cmd()
    fb = _fb(connected=False)
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb, True)  # consume startup
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 0.1, now2, fb, False)
    assert safe.motion_mode == "STOP"
    assert state.last_stop_reason == "communication_lost"


# ------------------------------------------------------------------
#  Hardware mode: feedback timeout → STOP
# ------------------------------------------------------------------

def test_hardware_mode_feedback_timeout_stop():
    mgr = _manager(simulation_mode=False)
    raw = _cmd()
    fb_stale = _fb(stamp_sec=time.time() - 2.0)
    now = time.time()
    mgr.evaluate(raw, now - 0.1, now, fb_stale, True)  # consume startup
    now2 = time.time()
    safe, state = mgr.evaluate(raw, now2 - 0.1, now2, fb_stale, True)
    assert safe.motion_mode == "STOP"
    assert state.last_stop_reason == "feedback_timeout"


# ------------------------------------------------------------------
#  Shutdown command
# ------------------------------------------------------------------

def test_shutdown_stop():
    mgr = _manager()
    cmd = mgr.shutdown()
    assert cmd.motion_mode == "STOP"
    assert cmd.safe_stop is True
    assert cmd.stop_reason == "shutdown"
