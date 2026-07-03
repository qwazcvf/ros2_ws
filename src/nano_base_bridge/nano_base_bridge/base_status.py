"""
base_status.py — Generates diagnostic_msgs/DiagnosticArray for /base/status.

Phase 1 key-value fields include:
  mode, motion_mode, speed_mps, steering_angle_rad,
  cmd_vel_alive, cmd_vel_timeout, hardware_connected,
  feedback_alive, feedback_timeout, estop_active,
  battery_voltage, error_code, last_stop_reason,
  battery_percentage, error_text, odom_x, odom_y, odom_yaw,
  control_rate_hz, simulation_mode.
"""

from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue


class BaseStatusPublisher:
    """Builds and populates DiagnosticArray messages for /base/status."""

    def __init__(self):
        self._seq = 0

    def build(
        self,
        stamp,
        simulation_mode: bool,
        motion_mode: str,
        speed_mps: float,
        steering_angle_rad: float,
        cmd_vel_alive: bool,
        cmd_vel_timeout: bool,
        hardware_connected: bool,
        feedback_alive: bool,
        feedback_timeout: bool,
        estop_active: bool,
        battery_voltage: float,
        battery_percentage: float,
        error_code: int,
        error_text: str,
        last_stop_reason: str,
        odom_x: float = 0.0,
        odom_y: float = 0.0,
        odom_yaw: float = 0.0,
        control_rate_hz: float = 50.0,
    ) -> DiagnosticArray:
        """Build a full DiagnosticArray message."""

        # --- Determine status level ---
        level = self._determine_level(
            cmd_vel_timeout=cmd_vel_timeout,
            feedback_timeout=feedback_timeout,
            hardware_connected=hardware_connected,
            simulation_mode=simulation_mode,
            estop_active=estop_active,
            error_code=error_code,
            battery_voltage=battery_voltage,
        )

        # --- Build key-value pairs ---
        values = [
            KeyValue(key="mode", value="simulation" if simulation_mode else "hardware"),
            KeyValue(key="simulation_mode", value=str(simulation_mode).lower()),
            KeyValue(key="motion_mode", value=motion_mode),
            KeyValue(key="speed_mps", value=f"{speed_mps:.4f}"),
            KeyValue(key="steering_angle_rad", value=f"{steering_angle_rad:.4f}"),
            KeyValue(key="cmd_vel_alive", value=str(cmd_vel_alive).lower()),
            KeyValue(key="cmd_vel_timeout", value=str(cmd_vel_timeout).lower()),
            KeyValue(key="hardware_connected", value=str(hardware_connected).lower()),
            KeyValue(key="feedback_alive", value=str(feedback_alive).lower()),
            KeyValue(key="feedback_timeout", value=str(feedback_timeout).lower()),
            KeyValue(key="estop_active", value=str(estop_active).lower()),
            KeyValue(key="battery_voltage", value=f"{battery_voltage:.2f}"),
            KeyValue(key="battery_percentage", value=f"{battery_percentage:.1f}"),
            KeyValue(key="error_code", value=str(error_code)),
            KeyValue(key="error_text", value=error_text),
            KeyValue(key="last_stop_reason", value=last_stop_reason),
            KeyValue(key="odom_x", value=f"{odom_x:.4f}"),
            KeyValue(key="odom_y", value=f"{odom_y:.4f}"),
            KeyValue(key="odom_yaw", value=f"{odom_yaw:.4f}"),
            KeyValue(key="control_rate_hz", value=f"{control_rate_hz:.1f}"),
        ]

        # --- Build status ---
        status = DiagnosticStatus(
            level=level,
            name="nano_base_bridge: Base Status",
            message=self._level_message(level),
            hardware_id="nano_base_bridge",
            values=values,
        )

        arr = DiagnosticArray()
        arr.header.stamp = stamp
        arr.header.frame_id = ""
        arr.status = [status]

        self._seq += 1
        return arr

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _determine_level(
        self,
        cmd_vel_timeout: bool,
        feedback_timeout: bool,
        hardware_connected: bool,
        simulation_mode: bool,
        estop_active: bool,
        error_code: int,
        battery_voltage: float,
    ) -> int:
        """Determine DiagnosticStatus level."""
        # ERROR conditions
        if estop_active:
            return DiagnosticStatus.ERROR
        if error_code != 0:
            return DiagnosticStatus.ERROR
        # Low-battery stop (reserved, disabled by default)
        if battery_voltage < 19.0:
            return DiagnosticStatus.ERROR

        # WARN conditions
        if cmd_vel_timeout:
            return DiagnosticStatus.WARN
        if feedback_timeout:
            return DiagnosticStatus.WARN
        if not hardware_connected and not simulation_mode:
            return DiagnosticStatus.WARN
        if battery_voltage < 21.0:
            return DiagnosticStatus.WARN

        # OK
        return DiagnosticStatus.OK

    @staticmethod
    def _level_message(level: int) -> str:
        if level == DiagnosticStatus.OK:
            return "Normal operation or safe stop"
        elif level == DiagnosticStatus.WARN:
            return "Warning: timeout, communication lost, or low battery"
        elif level == DiagnosticStatus.ERROR:
            return "Error: e-stop active, hardware error, or critical battery"
        return "Unknown"
