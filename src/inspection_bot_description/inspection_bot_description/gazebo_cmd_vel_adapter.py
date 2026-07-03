#!/usr/bin/env python3
"""
gazebo_cmd_vel_adapter — Phase 2A (low-speed Ackermann-like simulation).

Subscribes /cmd_vel (Twist), publishes:
  - /front_steering_controller/commands  (Float64MultiArray [fl, fr])
  - /drive_controller/commands           (Float64MultiArray [fl, fr, rl, rr])
  - /odom                                (Odometry)
  - odom -> base_link TF                 (TransformBroadcaster)

Rear steering is disabled (fixed at 0).
No crab, no spot-rotate, no 4-wheel independent steering.
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray, Header
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class GazeboCmdVelAdapter(Node):
    def __init__(self):
        super().__init__("gazebo_cmd_vel_adapter")

        # ── Parameters ──
        self.declare_parameter("wheelbase", 0.460)
        self.declare_parameter("track_width", 0.476)
        self.declare_parameter("wheel_radius", 0.076)
        self.declare_parameter("max_speed_mps", 0.10)
        self.declare_parameter("max_reverse_speed_mps", 0.05)
        self.declare_parameter("max_angular_speed_radps", 0.30)
        self.declare_parameter("max_steering_angle_rad", 0.60)
        self.declare_parameter("cmd_timeout_sec", 0.5)
        self.declare_parameter("odom_rate_hz", 30.0)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")

        self.wheelbase = self.get_parameter("wheelbase").value
        self.track_width = self.get_parameter("track_width").value
        self.wheel_radius = self.get_parameter("wheel_radius").value
        self.max_speed = self.get_parameter("max_speed_mps").value
        self.max_reverse = self.get_parameter("max_reverse_speed_mps").value
        self.max_angular = self.get_parameter("max_angular_speed_radps").value
        self.max_steer = self.get_parameter("max_steering_angle_rad").value
        self.timeout = self.get_parameter("cmd_timeout_sec").value
        self.odom_rate = self.get_parameter("odom_rate_hz").value
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value

        # ── State ──
        self.v = 0.0
        self.wz = 0.0
        self.last_cmd_time = self.get_clock().now()
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_odom_time = self.get_clock().now()

        # ── Publishers ──
        self.pub_front_steer = self.create_publisher(
            Float64MultiArray, "/front_steering_controller/commands", 10)
        self.pub_drive = self.create_publisher(
            Float64MultiArray, "/drive_controller/commands", 10)
        self.pub_odom = self.create_publisher(Odometry, "/odom", 10)

        # ── TF broadcaster ──
        self.tf_broadcaster = TransformBroadcaster(self)

        # ── Subscriber ──
        self.create_subscription(Twist, "/cmd_vel", self.cmd_callback, 10)

        # ── Timers ──
        self.control_timer = self.create_timer(0.02, self.control_loop)  # 50 Hz
        self.odom_timer = self.create_timer(1.0 / self.odom_rate, self.publish_odom)

        # ── Summary log ──
        self.get_logger().info("gazebo_cmd_vel_adapter started (Phase 2A)")
        self.get_logger().info("  subscribed: /cmd_vel")
        self.get_logger().info("  publishes: /front_steering_controller/commands")
        self.get_logger().info("  publishes: /drive_controller/commands")
        self.get_logger().info("  publishes: /odom")
        self.get_logger().info("  broadcasts: odom -> base_link")
        self.get_logger().info("  rear steering: disabled (fixed 0)")

    def cmd_callback(self, msg):
        self.v = msg.linear.x
        self.wz = msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def control_loop(self):
        now = self.get_clock().now()
        dt = (now - self.last_cmd_time).nanoseconds * 1e-9

        # Timeout check
        if dt > self.timeout:
            self.v = 0.0
            self.wz = 0.0

        # Clamp
        v = max(-self.max_reverse, min(self.max_speed, self.v))
        wz = max(-self.max_angular, min(self.max_angular, self.wz))

        # ── Pure angular with zero linear → no motion, no steering ──
        if abs(v) < 1e-4:
            steer_msg = Float64MultiArray()
            steer_msg.data = [0.0, 0.0]
            self.pub_front_steer.publish(steer_msg)

            drive_msg = Float64MultiArray()
            drive_msg.data = [0.0, 0.0, 0.0, 0.0]
            self.pub_drive.publish(drive_msg)
            return

        # ── Compute steering angles ──
        if abs(wz) < 1e-4:
            fl_angle = 0.0
            fr_angle = 0.0
        else:
            R = abs(v / wz)
            half_track = self.track_width / 2.0

            if wz > 0:  # left turn
                fl_angle = math.atan(self.wheelbase / (R - half_track))
                fr_angle = math.atan(self.wheelbase / (R + half_track))
            else:  # right turn
                fl_angle = -math.atan(self.wheelbase / (R + half_track))
                fr_angle = -math.atan(self.wheelbase / (R - half_track))

        # Clamp steering
        fl_angle = max(-self.max_steer, min(self.max_steer, fl_angle))
        fr_angle = max(-self.max_steer, min(self.max_steer, fr_angle))

        # ── Publish steering (front only) ──
        steer_msg = Float64MultiArray()
        steer_msg.data = [fl_angle, fr_angle]
        self.pub_front_steer.publish(steer_msg)

        # ── Publish drive (all 4 wheels) ──
        wheel_speed = v / self.wheel_radius
        drive_msg = Float64MultiArray()
        drive_msg.data = [wheel_speed] * 4
        self.pub_drive.publish(drive_msg)

        # ── Odometry integration ──
        now2 = self.get_clock().now()
        odom_dt = (now2 - self.last_odom_time).nanoseconds * 1e-9
        if odom_dt > 0.0 and odom_dt < 1.0:
            self.x += v * math.cos(self.yaw) * odom_dt
            self.y += v * math.sin(self.yaw) * odom_dt
            self.yaw += wz * odom_dt
        self.last_odom_time = now2

    def publish_odom(self):
        now = self.get_clock().now().to_msg()

        # TF
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        # Odometry message
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.wz
        self.pub_odom.publish(odom)


def main():
    rclpy.init()
    node = GazeboCmdVelAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
