#!/usr/bin/env python3
"""Publishes zero-position joint states for all 8 active joints."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

JOINT_NAMES = [
    "fl_steering_joint", "fr_steering_joint",
    "rl_steering_joint", "rr_steering_joint",
    "fl_wheel_joint", "fr_wheel_joint",
    "rl_wheel_joint", "rr_wheel_joint",
]


class StaticJointStatePublisher(Node):
    def __init__(self):
        super().__init__("static_joint_state_publisher")
        self.pub = self.create_publisher(JointState, "/joint_states", 10)
        self.timer = self.create_timer(0.05, self.publish)
        self.get_logger().info("Publishing zero joint states...")

    def publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = [0.0] * len(JOINT_NAMES)
        msg.velocity = [0.0] * len(JOINT_NAMES)
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = StaticJointStatePublisher()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
