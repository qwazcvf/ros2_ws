#!/usr/bin/env python3
"""
gazebo_cmd_vel_adapter — Phase 2A (low-speed Ackermann-like simulation).

Subscribes /cmd_vel (Twist), immediately computes Ackermann steering + wheel speeds,
publishes to ros2_control topics, /odom, and odom->base_link TF.

Rear steering: fixed at 0. No crab, no spot-rotate.
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray
from tf2_ros import TransformBroadcaster


class GazeboCmdVelAdapter(Node):
    def __init__(self):
        super().__init__("gazebo_cmd_vel_adapter")

        # ── Parameters ──
        self.declare_parameter("wheelbase", 0.460)
        self.declare_parameter("track_width", 0.476)
        self.declare_parameter("wheel_radius", 0.076)
        self.declare_parameter("max_speed_mps", 0.60)
        self.declare_parameter("max_reverse_speed_mps", 0.20)
        self.declare_parameter("max_angular_speed_radps", 1.50)
        self.declare_parameter("max_steering_angle_rad", 0.785)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")

        self.wb = self.get_parameter("wheelbase").value
        self.tw = self.get_parameter("track_width").value
        self.r  = self.get_parameter("wheel_radius").value
        self.max_v   = self.get_parameter("max_speed_mps").value
        self.max_rv  = self.get_parameter("max_reverse_speed_mps").value
        self.max_wz  = self.get_parameter("max_angular_speed_radps").value
        self.max_str = self.get_parameter("max_steering_angle_rad").value
        self.odom_frame_id = self.get_parameter("odom_frame").value
        self.base_frame_id = self.get_parameter("base_frame").value

        # ── State ──
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.prev_time = self.get_clock().now()

        # ── Publishers ──
        self.pub_steer = self.create_publisher(Float64MultiArray, "/front_steering_controller/commands", 10)
        self.pub_drive = self.create_publisher(Float64MultiArray, "/drive_controller/commands", 10)
        self.pub_odom  = self.create_publisher(Odometry, "/odom", 10)

        # ── TF ──
        self.tfb = TransformBroadcaster(self)

        # ── Subscriber (main loop: compute & publish on every /cmd_vel) ──
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)

        self.get_logger().info("gazebo_cmd_vel_adapter started (Phase 2A v2)")
        self.get_logger().info(f"  wheelbase={self.wb} track={self.tw} radius={self.r}")
        self.get_logger().info(f"  max_v={self.max_v} max_rv={self.max_rv} max_wz={self.max_wz} max_steer={self.max_str}")
        self.get_logger().info("  subscribed: /cmd_vel")
        self.get_logger().info("  publishes: /front_steering_controller/commands [fl, fr]")
        self.get_logger().info("  publishes: /drive_controller/commands [fl,fr,rl,rr]")
        self.get_logger().info("  publishes: /odom + odom->base_link TF")
        self.get_logger().info("  rear steering: disabled (fixed 0)")

    def on_cmd_vel(self, msg):
        v  = msg.linear.x
        wz = msg.angular.z

        # Clamp
        v  = max(-self.max_rv, min(self.max_v, v))
        wz = max(-self.max_wz, min(self.max_wz, wz))

        # Odom integration
        now = self.get_clock().now()
        dt = (now - self.prev_time).nanoseconds * 1e-9
        if dt > 0.0 and dt < 1.0 and abs(v) > 1e-4:
            self.x   += v * math.cos(self.yaw) * dt
            self.y   += v * math.sin(self.yaw) * dt
            self.yaw += wz * dt
        self.prev_time = now

        # ── Steering ──
        if abs(v) < 1e-4:
            # No motion → zero steering
            fl_angle = 0.0
            fr_angle = 0.0
        elif abs(wz) < 1e-4:
            # Straight
            fl_angle = 0.0
            fr_angle = 0.0
        else:
            R = abs(v / wz)
            ht = self.tw / 2.0
            if wz > 0:  # left turn
                fl_angle =  math.atan(self.wb / max(R - ht, 0.01))
                fr_angle =  math.atan(self.wb / (R + ht))
            else:       # right turn
                fl_angle = -math.atan(self.wb / (R + ht))
                fr_angle = -math.atan(self.wb / max(R - ht, 0.01))
            fl_angle = max(-self.max_str, min(self.max_str, fl_angle))
            fr_angle = max(-self.max_str, min(self.max_str, fr_angle))

        sm = Float64MultiArray()
        sm.data = [fl_angle, fr_angle]
        self.pub_steer.publish(sm)

        # ── Drive ──
        ws = v / self.r if abs(v) > 1e-4 else 0.0
        dm = Float64MultiArray()
        dm.data = [ws, ws, ws, ws]
        self.pub_drive.publish(dm)

        # ── Odom + TF ──
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = self.odom_frame_id
        t.child_frame_id = self.base_frame_id
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = math.sin(self.yaw / 2.0)
        t.transform.rotation.w = math.cos(self.yaw / 2.0)
        self.tfb.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = t.transform.rotation
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = wz
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
