"""
serial_transport.py — Serial (UART) chassis transport (SAFETY STUB).

Phase 1: This is a safety stub. No real serial protocol is implemented.
If pyserial is not installed (expected), the transport returns
hardware_connected=False and feedback_alive=False.

colcon build MUST NOT fail when pyserial is absent.
"""

import time
from .base_transport import BaseTransport
from ..protocol import BaseCommand, BaseFeedback


class SerialTransport(BaseTransport):
    """Serial transport stub — requires pyserial for real use."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, timeout: float = 0.05):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial = None
        self._connected = False
        self._serial_available = False

        # Lazy import — do NOT fail on missing pyserial
        try:
            import serial  # noqa: F401
            self._serial_available = True
        except ImportError:
            self._serial_available = False

    def connect(self) -> bool:
        if not self._serial_available:
            # No pyserial → cannot connect
            self._connected = False
            return False

        try:
            import serial
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout,
            )
            if self._serial.is_open:
                self._connected = True
                return True
        except Exception:
            self._connected = False

        self._connected = False
        return False

    def disconnect(self):
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        self._connected = False

    def is_connected(self) -> bool:
        if self._serial_available and self._serial is not None:
            try:
                return self._serial.is_open
            except Exception:
                return False
        return False

    def send_command(self, command: BaseCommand) -> bool:
        """Send command over serial. Returns False if not connected."""
        if not self.is_connected():
            return False
        # Phase 1 stub — no real protocol yet
        return False

    def read_feedback(self) -> BaseFeedback:
        """Read feedback from serial. Returns disconnected feedback if not available."""
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
