"""
Launch Inspection Bot in Ignition Gazebo (Fortress) with ros2_control.

Usage:
  ros2 launch inspection_bot_description gz_sim.launch.py
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = "inspection_bot_description"
    pkg_share = FindPackageShare(package=pkg_name).find(pkg_name)
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    xacro_file = os.path.join(pkg_share, "urdf", "robot.xacro")
    robot_desc_cmd = Command([FindExecutable(name="xacro"), " ", xacro_file])
    robot_description = {"robot_description": ParameterValue(robot_desc_cmd, value_type=str)}

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
    )

    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "inspection_bot", "-z", "0.3"],
        output="screen",
    )

    # Controller spawners (delayed until Gazebo plugin initializes)
    jsp = Node(
        package="controller_manager", executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )
    steer = Node(
        package="controller_manager", executable="spawner",
        arguments=["steering_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )
    drive = Node(
        package="controller_manager", executable="spawner",
        arguments=["drive_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    delay = TimerAction(period=8.0, actions=[jsp, steer, drive])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gz_sim,
        robot_state_pub,
        spawn,
        delay,
    ])
