"""
odom_integrator.py — Dead-reckoning odometry integrator.

SIMULATION mode:
  v = safe_command.speed_mps
  delta = safe_command.steering_angle_rad
  omega = v / wheel_base * tan(delta)

HARDWARE mode:
  v = feedback.speed_mps
  delta = feedback.steering_angle_rad
  BUT only if hardware_connected and feedback_alive.

Publishes nav_msgs/Odometry and TF odom → base_link.
"""

import math
import numpy as np

from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose, Point, Quaternion, Twist, Vector3, TransformStamped


def _make_quaternion(yaw: float) -> Quaternion:
    """Return a Quaternion from a yaw angle (rotation around Z)."""
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class OdomIntegrator:
    """Integrates velocity commands or feedback into odometry."""

    def __init__(self, params: dict):
        self._wheel_base = float(params.get("wheel_base_m", 0.55))
        self._odom_frame = str(params.get("odom_frame_id", "odom"))
        self._base_frame = str(params.get("base_frame_id", "base_link"))

        # Covariance
        pose_cov = params.get("odom_pose_covariance_diagonal", [0.05, 0.05, 9999.0, 9999.0, 9999.0, 0.20])
        twist_cov = params.get("odom_twist_covariance_diagonal", [0.05, 0.05, 9999.0, 9999.0, 9999.0, 0.20])

        self._pose_cov = list(map(float, pose_cov))
        self._twist_cov = list(map(float, twist_cov))

        # State
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0

        self._last_time = None

    # ------------------------------------------------------------------
    #  Integration
    # ------------------------------------------------------------------

    def update_from_safe_command(self, speed_mps: float, steering_angle_rad: float, stamp_sec: float):
        """Integrate using the safety-approved command (simulation mode)."""
        now = stamp_sec
        if self._last_time is None:
            self._last_time = now
            return

        dt = now - self._last_time
        if dt <= 0.0 or dt > 1.0:
            self._last_time = now
            return

        v = speed_mps
        delta = steering_angle_rad

        if abs(v) < 1e-9:
            # No speed → no integration
            self._last_time = now
            return

        omega = v / self._wheel_base * math.tan(delta)

        self._x += v * math.cos(self._yaw) * dt
        self._y += v * math.sin(self._yaw) * dt
        self._yaw += omega * dt

        # Keep yaw in [-pi, pi]
        self._yaw = math.atan2(math.sin(self._yaw), math.cos(self._yaw))

        self._last_time = now

    def update_from_feedback(self, speed_mps: float, steering_angle_rad: float, stamp_sec: float):
        """Integrate using real hardware feedback (hardware mode).

        IMPORTANT: Only call this when hardware_connected and feedback_alive
        are BOTH true. Otherwise do NOT integrate.
        """
        # Same integration formula, different data source
        self.update_from_safe_command(speed_mps, steering_angle_rad, stamp_sec)

    # ------------------------------------------------------------------
    #  Message builders
    # ------------------------------------------------------------------

    def build_odometry_msg(self, stamp, v: float = 0.0, omega: float = 0.0) -> Odometry:
        """Build a nav_msgs/Odometry message from current state."""
        msg = Odometry()

        msg.header.stamp = stamp
        msg.header.frame_id = self._odom_frame
        msg.child_frame_id = self._base_frame

        # Pose
        msg.pose.pose = Pose(
            position=Point(x=self._x, y=self._y, z=0.0),
            orientation=_make_quaternion(self._yaw),
        )
        # Covariance (6x6 flattened row-major)
        msg.pose.covariance = self._build_covariance_matrix(self._pose_cov)

        # Twist
        msg.twist.twist = Twist(
            linear=Vector3(x=v, y=0.0, z=0.0),
            angular=Vector3(x=0.0, y=0.0, z=omega),
        )
        msg.twist.covariance = self._build_covariance_matrix(self._twist_cov)

        return msg

    def build_tf_msg(self, stamp) -> TransformStamped:
        """Build a geometry_msgs/TransformStamped for odom → base_link."""
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = self._odom_frame
        t.child_frame_id = self._base_frame

        t.transform.translation.x = self._x
        t.transform.translation.y = self._y
        t.transform.translation.z = 0.0
        t.transform.rotation = _make_quaternion(self._yaw)

        return t

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_covariance_matrix(diagonal):
        """Build a 36-element covariance list from 6 diagonal values."""
        cov = [0.0] * 36
        for i in range(6):
            cov[i * 6 + i] = diagonal[i]
        return cov

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def yaw(self) -> float:
        return self._yaw
