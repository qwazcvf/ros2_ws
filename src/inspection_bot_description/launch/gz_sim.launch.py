"""
Phase 2A — Gazebo simulation with cmd_vel adapter.

Starts:
  1. Ignition Gazebo Fortress
  2. robot_state_publisher
  3. Spawn robot
  4. Controller spawners (front_steering, drive, joint_state_broadcaster)
  5. gazebo_cmd_vel_adapter

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

    # 1. Ignition Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
    )

    # 2. robot_state_publisher
    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # 3. Spawn robot
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "inspection_bot", "-z", "0.3"],
        output="screen",
    )

    # 4. Controller spawners (delayed 3s until Gazebo plugin initializes)
    jsp = Node(
        package="controller_manager", executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )
    front_steer = Node(
        package="controller_manager", executable="spawner",
        arguments=["front_steering_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )
    drive = Node(
        package="controller_manager", executable="spawner",
        arguments=["drive_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
    )
    delay_ctrl = TimerAction(period=3.0, actions=[jsp, front_steer, drive])

    # 5. gazebo_cmd_vel_adapter (delayed 5s)
    adapter = Node(
        package="inspection_bot_description",
        executable="gazebo_cmd_vel_adapter",
        name="gazebo_cmd_vel_adapter",
        output="screen",
        parameters=[{
            "use_sim_time": True,
            "wheelbase": 0.460,
            "track_width": 0.476,
            "wheel_radius": 0.076,
            "max_speed_mps": 0.10,
            "max_reverse_speed_mps": 0.05,
            "max_angular_speed_radps": 0.30,
            "max_steering_angle_rad": 0.785,
            "odom_frame": "odom",
            "base_frame": "base_link",
        }],
    )
    delay_adapter = TimerAction(period=5.0, actions=[adapter])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gz_sim,
        robot_state_pub,
        spawn,
        delay_ctrl,
        delay_adapter,
    ])
