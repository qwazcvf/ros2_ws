"""
can_transport.py — CAN bus chassis transport (SAFETY STUB).

Phase 1: This is a safety stub. No real CAN protocol is implemented.
If python-can is not installed (expected), the transport returns
hardware_connected=False and feedback_alive=False.

colcon build MUST NOT fail when python-can is absent.
"""

import time
from .base_transport import BaseTransport
from ..protocol import BaseCommand, BaseFeedback


class CanTransport(BaseTransport):
    """CAN transport stub — requires python-can for real use."""

    def __init__(self, interface: str = "can0", bitrate: int = 500000):
        self._interface = interface
        self._bitrate = bitrate
        self._bus = None
        self._connected = False
        self._can_available = False

        # Lazy import — do NOT fail on missing python-can
        try:
            import can  # noqa: F401
            self._can_available = True
        except ImportError:
            self._can_available = False

    def connect(self) -> bool:
        if not self._can_available:
            self._connected = False
            return False

        try:
            import can
            self._bus = can.interface.Bus(
                interface=self._interface,
                bitrate=self._bitrate,
            )
            self._connected = True
            return True
        except Exception:
            self._connected = False

        self._connected = False
        return False

    def disconnect(self):
        if self._bus is not None:
            try:
                self._bus.shutdown()
            except Exception:
                pass
            self._bus = None
        self._connected = False

    def is_connected(self) -> bool:
        if self._can_available and self._bus is not None:
            return True
        return False

    def send_command(self, command: BaseCommand) -> bool:
        """Send command over CAN. Returns False if not connected."""
        if not self.is_connected():
            return False
        # Phase 1 stub — no real protocol yet
        return False

    def read_feedback(self) -> BaseFeedback:
        """Read feedback from CAN. Returns disconnected feedback if not available."""
        if not self.is_connected():
            return BaseFeedback(
                speed_mps=0.0,
                steering_angle_rad=0.0,
                battery_voltage=24.0,
                battery_percentage=100.0,
                estop_active=False,
                error_code=0,
                error_text="",
                connected=False,
                stamp_sec=time.time(),
            )
        # Phase 1 stub — no real protocol yet
        return BaseFeedback(
            speed_mps=0.0,
            steering_angle_rad=0.0,
            battery_voltage=24.0,
            battery_percentage=100.0,
            estop_active=False,
            error_code=0,
            error_text="",
            connected=False,
            stamp_sec=time.time(),
        )
