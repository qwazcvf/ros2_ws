#!/usr/bin/env python3
"""
订阅 /cloud_registered，每 2 秒保存一次 PCD，Ctrl+C 时保存最终版。

用法:
    cd ~/ros2_ws
    python3 save_pcd.py

输出:
    maps/final.pcd       最终完整点云（退出时保存）
    maps/snapshot_*.pcd  每 2 秒的快照（可选）
"""

import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np
import open3d as o3d


class PCDSaver(Node):
    def __init__(self):
        super().__init__('pcd_saver')
        self.all_points = []  # 累积所有点
        self.last_save_time = self.get_clock().now()

        self.create_subscription(PointCloud2, '/cloud_registered', self.cb, 10)
        self.timer = self.create_timer(2.0, self.snapshot)  # 每2秒存一次快照

        self.out_dir = os.path.join(os.path.expanduser('~'), 'ros2_ws', 'maps')
        os.makedirs(self.out_dir, exist_ok=True)

        self.get_logger().info('💾 PCD Saver 已启动，每2秒保存快照')

    def cb(self, msg):
        pts = list(pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True))
        self.all_points.extend(pts)
        self.get_logger().info(f'  已累积 {len(self.all_points)} 点', throttle_duration_sec=5)

    def _save_pcd(self, path):
        pts = np.array(self.all_points, dtype=np.float64)
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        o3d.io.write_point_cloud(path, pcd)
        return pts.shape[0]

    def snapshot(self):
        if len(self.all_points) < 1000:
            return
        path = os.path.join(self.out_dir, 'latest.pcd')
        n = self._save_pcd(path)
        self.get_logger().info(f'📸 已保存 {n} 点 → {path}', throttle_duration_sec=2)

    def save_final(self):
        if len(self.all_points) < 1000:
            self.get_logger().warn('点太少，未保存')
            return
        path = os.path.join(self.out_dir, 'final.pcd')
        n = self._save_pcd(path)
        self.get_logger().info(f'✅ 最终地图已保存: {n} 点 → {path}')


def main():
    rclpy.init()
    node = PCDSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.save_final()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
