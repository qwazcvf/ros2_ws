import os
import subprocess

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Run unitree lidar
    node1 = Node(
        package='unitree_lidar_ros2',
        executable='unitree_lidar_ros2_node',
        name='unitree_lidar_ros2_node',
        output='screen',
        parameters= [
                
                # ===== UDP 模式 (网线连接) =====
                {'initialize_type': 2},
                {'work_mode': 0},
                {'use_system_timestamp': True},
                {'range_min': 0.0},
                {'range_max': 100.0},
                {'cloud_scan_num': 18},

                # 以下参数在 UDP 模式下忽略
                {'serial_port': '/dev/ttyACM0'},
                {'baudrate': 4000000},

                # UDP 网络配置
                {'lidar_port': 6101},
                {'lidar_ip': '192.168.1.62'},       # 雷达的出厂 IP
                {'local_port': 6201},
                {'local_ip': '192.168.1.2'},         # Jetson 网口的 IP
                
                {'cloud_frame': "unilidar_lidar"},
                {'cloud_topic': "unilidar/cloud"},
                {'imu_frame': "unilidar_imu"},
                {'imu_topic': "unilidar/imu"},
                ]
    )

    # 不再启动 RViz（由 SLAM 脚本负责可视化）
    # 只跑雷达驱动节点，稳定可靠
    return LaunchDescription([node1])
