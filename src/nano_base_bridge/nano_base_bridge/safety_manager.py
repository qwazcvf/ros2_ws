"""
safety_manager.py — Enforces safety constraints on every command.

All commands sent to the chassis MUST pass through this manager.
Inputs: raw_command (BaseCommand), timestamps, feedback, transport state.
Outputs: safe_command (BaseCommand), safety_state (SafetyState).
"""

import time
from .protocol import BaseCommand, BaseFeedback, SafetyState


class SafetyManager:
    """Safety gate that enforces timeouts, limits, and connection checks."""

    def __init__(self, params: dict):
        self._max_speed = float(params.get("max_speed_mps", 0.10))
        self._max_reverse = float(params.get("max_reverse_speed_mps", 0.05))
        self._max_steering = float(params.get("max_steering_angle_rad", 0.35))
        self._cmd_vel_timeout = float(params.get("cmd_vel_timeout_sec", 0.5))
        self._feedback_timeout = float(params.get("hardware_feedback_timeout_sec", 0.5))
        self._comm_timeout = float(params.get("communication_timeout_sec", 0.5))
        self._send_stop_on_startup = bool(params.get("send_stop_on_startup", True))
        self._send_stop_on_shutdown = bool(params.get("send_stop_on_shutdown", True))
        self._stop_on_estop = bool(params.get("stop_on_estop", True))
        self._simulation_mode = bool(params.get("simulation_mode", True))

        # Track startup
        self._startup = True

    def evaluate(
        self,
        raw_command: BaseCommand,
        last_cmd_vel_time: float,
        current_time: float,
        feedback: BaseFeedback,
        transport_connected: bool,
    ):
        """
        Evaluate safety and produce safe_command + safety_state.

        Returns:
            (safe_command: BaseCommand, safety_state: SafetyState)
        """
        state = SafetyState()
        stop_reason = ""

        # --- Determine liveness ---
        dt_cmd = current_time - last_cmd_vel_time if last_cmd_vel_time > 0 else 999.0
        dt_fb = current_time - feedback.stamp_sec if feedback.stamp_sec > 0 else 0.0

        state.cmd_vel_alive = dt_cmd < self._cmd_vel_timeout
        state.cmd_vel_timeout = not state.cmd_vel_alive
        state.hardware_connected = transport_connected or self._simulation_mode
        state.feedback_alive = (dt_fb < self._feedback_timeout) if not self._simulation_mode else True
        state.feedback_timeout = not state.feedback_alive
        state.estop_active = feedback.estop_active

        # --- Build default STOP command ---
        stop_cmd = BaseCommand(
            speed_mps=0.0,
            steering_angle_rad=0.0,
            motion_mode="STOP",
            stamp_sec=current_time,
            safe_stop=True,
            stop_reason="",
        )

        # --- Safety checks in priority order ---

        # 1. Startup: always STOP
        if self._startup and self._send_stop_on_startup:
            self._startup = False
            stop_cmd.stop_reason = "startup"
            state.last_stop_reason = "startup"
            return stop_cmd, state

        # 2. E-stop active
        if self._stop_on_estop and feedback.estop_active:
            stop_cmd.stop_reason = "estop_active"
            state.last_stop_reason = "estop_active"
            return stop_cmd, state

        # 3. cmd_vel timeout
        if state.cmd_vel_timeout:
            stop_cmd.stop_reason = "cmd_vel_timeout"
            state.last_stop_reason = "cmd_vel_timeout"
            return stop_cmd, state

        # 4. Hardware not connected (only enforced in non-simulation mode)
        if not state.hardware_connected and not self._simulation_mode:
            stop_cmd.stop_reason = "communication_lost"
            state.last_stop_reason = "communication_lost"
            return stop_cmd, state

        # 5. Feedback timeout (only enforced in non-simulation mode)
        if state.feedback_timeout and not self._simulation_mode:
            stop_cmd.stop_reason = "feedback_timeout"
            state.last_stop_reason = "feedback_timeout"
            return stop_cmd, state

        # --- Enforce speed / steering limits on the raw command ---
        safe = BaseCommand(
            speed_mps=raw_command.speed_mps,
            steering_angle_rad=raw_command.steering_angle_rad,
            motion_mode=raw_command.motion_mode,
            stamp_sec=current_time,
            safe_stop=False,
            stop_reason="",
        )

        # Speed limit
        safe.speed_mps = max(-self._max_reverse, min(self._max_speed, safe.speed_mps))

        # Steering limit
        safe.steering_angle_rad = max(
            -self._max_steering, min(self._max_steering, safe.steering_angle_rad)
        )

        state.last_stop_reason = ""

        return safe, state

    def shutdown(self) -> BaseCommand:
        """Return a STOP command for shutdown."""
        return BaseCommand(
            speed_mps=0.0,
            steering_angle_rad=0.0,
            motion_mode="STOP",
            stamp_sec=time.time(),
            safe_stop=True,
            stop_reason="shutdown",
        )

    @property
    def startup(self) -> bool:
        return self._startup
