"""
RViz-only launch — no simulator needed.

Usage:
  ros2 launch inspection_bot_description view_model.launch.py
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = "inspection_bot_description"
    pkg_share = FindPackageShare(package=pkg_name).find(pkg_name)
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")

    xacro_file = os.path.join(pkg_share, "urdf", "robot.xacro")
    robot_desc_cmd = Command([FindExecutable(name="xacro"), " ", xacro_file])
    robot_description = {"robot_description": ParameterValue(robot_desc_cmd, value_type=str)}

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # Built-in static joint state publisher (no GUI dependency)
    joint_state_pub = Node(
        package="inspection_bot_description",
        executable="static_joint_state_publisher",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    rviz_config = os.path.join(pkg_share, "rviz", "display.rviz")
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        robot_state_publisher,
        joint_state_pub,
        rviz,
    ])
