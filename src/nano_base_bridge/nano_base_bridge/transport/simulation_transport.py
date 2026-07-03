"""
simulation_transport.py — Simulated chassis transport.

Does NOT connect to real hardware.
Always returns connected=True, feedback_alive=True.
Uses the last safe_command to produce simulated BaseFeedback.
"""

import time
from .base_transport import BaseTransport
from ..protocol import BaseCommand, BaseFeedback


class SimulationTransport(BaseTransport):
    """Simulated transport — always connected, always alive."""

    def __init__(self):
        self._connected = False
        self._last_command = BaseCommand()

    # ------------------------------------------------------------------
    #  Transport interface
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def send_command(self, command: BaseCommand) -> bool:
        """Store the command for feedback simulation."""
        self._last_command = command
        return True

    def read_feedback(self) -> BaseFeedback:
        """Return simulated feedback based on last command."""
        return BaseFeedback(
            speed_mps=self._last_command.speed_mps,
            steering_angle_rad=self._last_command.steering_angle_rad,
            encoder_front_left=0,
            encoder_front_right=0,
            encoder_rear_left=0,
            encoder_rear_right=0,
            imu_yaw=0.0,
            imu_yaw_rate=0.0,
            battery_voltage=24.0,
            battery_percentage=100.0,
            estop_active=False,
            error_code=0,
            error_text="",
            connected=True,
            stamp_sec=time.time(),
        )
