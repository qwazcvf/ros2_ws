"""
ackermann_mapper.py — Converts /cmd_vel (Twist) to a low-speed Ackermann-equivalent command.

Uses only Twist.linear.x and Twist.angular.z.
All other fields (linear.y, linear.z, angular.x, angular.y) are ignored.

Output is a BaseCommand dataclass (not a ROS message).
"""

import math
from .protocol import BaseCommand


class AckermannMapper:
    """Maps Twist → low-speed Ackermann command with deadband, clamping, and mode detection."""

    # --- Motion mode constants ---
    MODE_STOP = "STOP"
    MODE_FORWARD = "FORWARD"
    MODE_BACKWARD = "BACKWARD"
    MODE_LEFT = "LEFT"
    MODE_RIGHT = "RIGHT"

    def __init__(self, params: dict):
        """
        Parameters expected (flat dict):
          wheel_base_m, max_speed_mps, max_reverse_speed_mps,
          max_angular_speed_radps, max_steering_angle_rad,
          linear_deadband_mps, angular_deadband_radps,
          min_speed_for_ackermann_mps,
          allow_stationary_steering, allow_pure_angular_crawl,
          pure_angular_crawl_speed_mps,
          invert_speed, invert_steering,
        """
        self._wheel_base = float(params.get("wheel_base_m", 0.55))
        self._max_speed = float(params.get("max_speed_mps", 0.10))
        self._max_reverse = float(params.get("max_reverse_speed_mps", 0.05))
        self._max_angular = float(params.get("max_angular_speed_radps", 0.50))
        self._max_steering = float(params.get("max_steering_angle_rad", 0.35))
        self._linear_deadband = float(params.get("linear_deadband_mps", 0.02))
        self._angular_deadband = float(params.get("angular_deadband_radps", 0.03))
        self._min_speed_for_ackermann = float(params.get("min_speed_for_ackermann_mps", 0.05))
        self._allow_stationary_steering = bool(params.get("allow_stationary_steering", False))
        self._allow_pure_angular_crawl = bool(params.get("allow_pure_angular_crawl", False))
        self._pure_angular_crawl_speed = float(params.get("pure_angular_crawl_speed_mps", 0.0))
        self._invert_speed = bool(params.get("invert_speed", False))
        self._invert_steering = bool(params.get("invert_steering", False))

    def map(self, linear_x: float, angular_z: float, stamp_sec: float = 0.0) -> BaseCommand:
        """
        Convert a single Twist (linear.x, angular.z) into a BaseCommand.
        """
        # --- Apply deadbands ---
        v = linear_x
        w = angular_z

        if abs(v) < self._linear_deadband:
            v = 0.0
        if abs(w) < self._angular_deadband:
            w = 0.0

        # --- Clamp velocities ---
        v = max(-self._max_reverse, min(self._max_speed, v))
        w = max(-self._max_angular, min(self._max_angular, w))

        # --- Direction inversion (config-driven, no code change) ---
        if self._invert_speed:
            v = -v
        if self._invert_steering:
            w = -w

        # --- Determine motion mode ---
        mode = self._determine_mode(v, w)

        # --- Compute steering angle ---
        steering = self._compute_steering(v, w, mode)

        cmd = BaseCommand(
            speed_mps=v,
            steering_angle_rad=steering,
            motion_mode=mode,
            stamp_sec=stamp_sec,
            safe_stop=False,
            stop_reason="",
        )
        return cmd

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _determine_mode(self, v: float, w: float) -> str:
        """Determine motion mode from clamped v, w."""
        if abs(v) < 1e-9 and abs(w) < 1e-9:
            return self.MODE_STOP

        # Pure angular with zero linear — critical safety case
        if abs(v) < 1e-9 and abs(w) >= 1e-9:
            if self._allow_stationary_steering:
                # Reserved: allow stationary steering but NO speed
                if w > 0:
                    return self.MODE_LEFT
                else:
                    return self.MODE_RIGHT
            elif self._allow_pure_angular_crawl:
                # Reserved: tiny crawl speed — not used in Phase 1
                crawl = self._pure_angular_crawl_speed
                if w > 0:
                    return self.MODE_LEFT
                else:
                    return self.MODE_RIGHT
            else:
                # Phase 1 default: STOP — no stationary steering
                return self.MODE_STOP

        # With forward/backward speed
        if v > 0:
            if w > 1e-9:
                return self.MODE_LEFT
            elif w < -1e-9:
                return self.MODE_RIGHT
            else:
                return self.MODE_FORWARD
        else:  # v < 0
            if w > 1e-9:
                return self.MODE_LEFT
            elif w < -1e-9:
                return self.MODE_RIGHT
            else:
                return self.MODE_BACKWARD

    def _compute_steering(self, v: float, w: float, mode: str) -> float:
        """Compute Ackermann-equivalent steering angle.

        steering = atan(wheel_base * w / v)

        Only computed when |v| >= min_speed_for_ackermann.
        """
        if mode == self.MODE_STOP:
            return 0.0

        if abs(v) < self._min_speed_for_ackermann:
            # Not enough speed for meaningful Ackermann steering
            return 0.0

        # Ackermann: delta = atan(L * omega / v)
        raw_steering = math.atan(self._wheel_base * w / v)

        # Clamp to max steering angle
        steering = max(-self._max_steering, min(self._max_steering, raw_steering))

        return steering
