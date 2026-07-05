#!/usr/bin/env python3
"""Normalizes /scan_raw frame_id to lidar_link (Fortress bridge compat)."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class ScanFrameNormalizer(Node):
    def __init__(self):
        super().__init__("scan_frame_normalizer")
        self.pub = self.create_publisher(LaserScan, "/scan", 10)
        self.sub = self.create_subscription(LaserScan, "/scan_raw", self.cb, 10)
        self.get_logger().info("Normalizing /scan_raw -> /scan (frame_id=lidar_link)")

    def cb(self, msg):
        msg.header.frame_id = "lidar_link"
        self.pub.publish(msg)

def main():
    rclpy.init()
    rclpy.spin(ScanFrameNormalizer())

if __name__ == "__main__":
    main()
