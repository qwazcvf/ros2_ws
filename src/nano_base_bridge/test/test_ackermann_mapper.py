"""
Unit tests for ackermann_mapper.py.
"""

import pytest
from nano_base_bridge.ackermann_mapper import AckermannMapper
from nano_base_bridge.protocol import BaseCommand

# Default safe params
DEFAULT_PARAMS = {
    "wheel_base_m": 0.55,
    "max_speed_mps": 0.10,
    "max_reverse_speed_mps": 0.05,
    "max_angular_speed_radps": 0.50,
    "max_steering_angle_rad": 0.35,
    "linear_deadband_mps": 0.02,
    "angular_deadband_radps": 0.03,
    "min_speed_for_ackermann_mps": 0.05,
    "allow_stationary_steering": False,
    "allow_pure_angular_crawl": False,
    "pure_angular_crawl_speed_mps": 0.0,
    "invert_speed": False,
    "invert_steering": False,
}


def _mapper(**overrides):
    p = dict(DEFAULT_PARAMS)
    p.update(overrides)
    return AckermannMapper(p)


# ------------------------------------------------------------------
#  STOP command
# ------------------------------------------------------------------

def test_stop():
    m = _mapper()
    cmd = m.map(0.0, 0.0)
    assert cmd.motion_mode == "STOP"
    assert cmd.speed_mps == 0.0
    assert cmd.steering_angle_rad == 0.0


# ------------------------------------------------------------------
#  Forward
# ------------------------------------------------------------------

def test_forward():
    m = _mapper()
    cmd = m.map(0.08, 0.0)
    assert cmd.motion_mode == "FORWARD"
    assert cmd.speed_mps == pytest.approx(0.08)
    assert cmd.steering_angle_rad == 0.0


# ------------------------------------------------------------------
#  Backward
# ------------------------------------------------------------------

def test_backward():
    m = _mapper()
    cmd = m.map(-0.04, 0.0)
    assert cmd.motion_mode == "BACKWARD"
    assert cmd.speed_mps == pytest.approx(-0.04)
    assert cmd.steering_angle_rad == 0.0


# ------------------------------------------------------------------
#  Left turn
# ------------------------------------------------------------------

def test_left():
    m = _mapper()
    cmd = m.map(0.08, 0.30)
    assert cmd.motion_mode == "LEFT"
    assert cmd.steering_angle_rad > 0


# ------------------------------------------------------------------
#  Right turn
# ------------------------------------------------------------------

def test_right():
    m = _mapper()
    cmd = m.map(0.08, -0.30)
    assert cmd.motion_mode == "RIGHT"
    assert cmd.steering_angle_rad < 0


# ------------------------------------------------------------------
#  Speed limit (forward)
# ------------------------------------------------------------------

def test_speed_limit_forward():
    m = _mapper()
    cmd = m.map(2.0, 0.0)
    assert cmd.speed_mps <= 0.10


# ------------------------------------------------------------------
#  Reverse speed limit
# ------------------------------------------------------------------

def test_reverse_speed_limit():
    m = _mapper()
    cmd = m.map(-2.0, 0.0)
    assert cmd.speed_mps >= -0.05


# ------------------------------------------------------------------
#  Steering angle limit
# ------------------------------------------------------------------

def test_steering_limit():
    m = _mapper()
    cmd = m.map(0.08, 2.0)
    assert abs(cmd.steering_angle_rad) <= 0.35


# ------------------------------------------------------------------
#  Deadband: small linear
# ------------------------------------------------------------------

def test_linear_deadband():
    m = _mapper()
    cmd = m.map(0.01, 0.0)
    assert cmd.speed_mps == 0.0


# ------------------------------------------------------------------
#  Deadband: small angular
# ------------------------------------------------------------------

def test_angular_deadband():
    m = _mapper()
    cmd = m.map(0.08, 0.02)
    # Angular deadband = 0.03, so 0.02 should be zeroed
    assert cmd.steering_angle_rad == 0.0


# ------------------------------------------------------------------
#  Pure angular.z default STOP (no stationary steering)
# ------------------------------------------------------------------

def test_pure_angular_stop_by_default():
    m = _mapper()
    cmd = m.map(0.0, 0.50)
    assert cmd.motion_mode == "STOP"
    assert cmd.speed_mps == 0.0
    assert cmd.steering_angle_rad == 0.0


# ------------------------------------------------------------------
#  Pure angular.z with allow_pure_angular_crawl (reserved)
# ------------------------------------------------------------------

def test_pure_angular_crawl_reserved():
    m = _mapper(allow_pure_angular_crawl=True, pure_angular_crawl_speed_mps=0.0)
    cmd = m.map(0.0, 0.50)
    # Even with crawl enabled, crawl_speed=0 still means stop for speed purposes
    assert cmd.motion_mode in ("LEFT", "RIGHT")


# ------------------------------------------------------------------
#  Max speed default is 0.10
# ------------------------------------------------------------------

def test_default_max_speed():
    m = _mapper()
    assert m._max_speed == 0.10


# ------------------------------------------------------------------
#  Max reverse speed default is 0.05
# ------------------------------------------------------------------

def test_default_max_reverse():
    m = _mapper()
    assert m._max_reverse == 0.05
