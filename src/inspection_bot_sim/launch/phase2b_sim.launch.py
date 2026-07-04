"""Phase 2B-1: Gazebo with factory world, 2D /scan bridge."""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc_share = FindPackageShare("inspection_bot_description").find("inspection_bot_description")
    sim_share  = FindPackageShare("inspection_bot_sim").find("inspection_bot_sim")
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    xacro_file = os.path.join(desc_share, "urdf", "robot.xacro")
    robot_desc = {"robot_description": ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]), value_type=str)}

    world_file = os.path.join(sim_share, "worlds", "phase2b_simple.sdf")

    # Gazebo with factory world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={"gz_args": f"-r {world_file}"}.items(),
    )

    rsp = Node(package="robot_state_publisher", executable="robot_state_publisher",
               output="both", parameters=[robot_desc, {"use_sim_time": use_sim_time}])

    spawn = Node(package="ros_gz_sim", executable="create",
                 arguments=["-topic", "robot_description", "-name", "inspection_bot", "-z", "0.3"],
                 output="screen")

    jsp = Node(package="controller_manager", executable="spawner",
               arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
               parameters=[{"use_sim_time": use_sim_time}])
    fs = Node(package="controller_manager", executable="spawner",
              arguments=["front_steering_controller", "-c", "/controller_manager"],
              parameters=[{"use_sim_time": use_sim_time}])
    dr = Node(package="controller_manager", executable="spawner",
              arguments=["drive_controller", "-c", "/controller_manager"],
              parameters=[{"use_sim_time": use_sim_time}])
    delay_ctrl = TimerAction(period=3.0, actions=[jsp, fs, dr])

    adapter = Node(package="inspection_bot_description", executable="gazebo_cmd_vel_adapter",
                   name="gazebo_cmd_vel_adapter", output="screen",
                   parameters=[{"use_sim_time": True, "wheelbase": 0.460, "track_width": 0.476,
                                "wheel_radius": 0.076, "max_speed_mps": 0.10, "max_reverse_speed_mps": 0.05,
                                "max_angular_speed_radps": 0.30, "max_steering_angle_rad": 0.785,
                                "odom_frame": "odom", "base_frame": "base_link"}])
    delay_adapter = TimerAction(period=5.0, actions=[adapter])

    bridge = Node(package="ros_gz_bridge", executable="parameter_bridge", name="bridge_scan",
                  output="screen",
                  arguments=["/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan"],
                  parameters=[{"use_sim_time": use_sim_time}])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gz_sim, rsp, spawn, delay_ctrl, delay_adapter, bridge,
    ])
