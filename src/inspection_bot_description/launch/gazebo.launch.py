"""
Classic Gazebo 11 launch file — NOT FOR THIS PLATFORM (Jetson ARM64).

This file is kept for reference. Classic Gazebo 11 is not available on
Jetson ARM64 and cannot be installed via apt.

To run simulation on this Jetson, use IGNITION GAZEBO instead:
  ros2 launch inspection_bot_description gz_sim.launch.py

If you are on x86_64 with Classic Gazebo 11 installed:
  1. Change the URDF <gazebo> plugin:
     filename="libgazebo_ros2_control.so"
     name="gazebo_ros2_control"
  2. Change <ros2_control> hardware plugin:
     <plugin>gazebo_ros2_control/GazeboSystem</plugin>
  3. Use gazebo_ros spawn_entity.py instead of ros_gz_sim create
"""
import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_name = "inspection_bot_description"

    msg = """
╔══════════════════════════════════════════════════════════════╗
║  Classic Gazebo 11 is NOT available on Jetson ARM64.        ║
║                                                             ║
║  Please use Ignition Gazebo instead:                        ║
║    ros2 launch inspection_bot_description gz_sim.launch.py  ║
║                                                             ║
║  This launch file is a placeholder for x86_64 systems.      ║
╚══════════════════════════════════════════════════════════════╝
"""
    return LaunchDescription([
        LogInfo(msg=msg),
        LogInfo(msg="Exiting. Use gz_sim.launch.py instead."),
    ])
