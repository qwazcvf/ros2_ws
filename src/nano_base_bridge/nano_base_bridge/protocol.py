"""
protocol.py — Internal data structures for the nano base bridge.

Defines dataclass structures for commands, feedback, and safety state.
No custom ROS messages are used.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BaseCommand:
    """Command sent to the chassis (after safety processing)."""

    speed_mps: float = 0.0
    steering_angle_rad: float = 0.0
    motion_mode: str = "STOP"
    stamp_sec: float = 0.0
    safe_stop: bool = False
    stop_reason: str = ""


@dataclass
class BaseFeedback:
    """Feedback received from the chassis (real or simulated)."""

    speed_mps: float = 0.0
    steering_angle_rad: float = 0.0
    encoder_front_left: int = 0
    encoder_front_right: int = 0
    encoder_rear_left: int = 0
    encoder_rear_right: int = 0
    imu_yaw: float = 0.0
    imu_yaw_rate: float = 0.0
    battery_voltage: float = 24.0
    battery_percentage: float = 100.0
    estop_active: bool = False
    error_code: int = 0
    error_text: str = ""
    connected: bool = True
    stamp_sec: float = 0.0


@dataclass
class SafetyState:
    """Current safety state snapshot."""

    cmd_vel_alive: bool = False
    cmd_vel_timeout: bool = False
    hardware_connected: bool = False
    feedback_alive: bool = False
    feedback_timeout: bool = False
    estop_active: bool = False
    last_stop_reason: str = ""
