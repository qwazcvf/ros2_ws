"""
base_bridge.launch.py — Launch the nano_base_bridge_node.

Usage:
  ros2 launch nano_base_bridge base_bridge.launch.py
  ros2 launch nano_base_bridge base_bridge.launch.py simulation_mode:=true
  ros2 launch nano_base_bridge base_bridge.launch.py simulation_mode:=false

Does NOT launch Nav2, LiDAR, SLAM, RViz, or Gazebo.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("nano_base_bridge")
    config_path = os.path.join(pkg_share, "config", "base_params.yaml")

    # Launch arguments
    simulation_mode_arg = DeclareLaunchArgument(
        "simulation_mode",
        default_value="true",
        description="Run in simulation mode (true) or hardware mode (false)",
    )

    # Node
    nano_base_bridge_node = Node(
        package="nano_base_bridge",
        executable="nano_base_bridge_node",
        name="nano_base_bridge_node",
        output="screen",
        parameters=[
            config_path,
            {"simulation_mode": LaunchConfiguration("simulation_mode")},
        ],
    )

    return LaunchDescription([
        simulation_mode_arg,
        nano_base_bridge_node,
    ])
