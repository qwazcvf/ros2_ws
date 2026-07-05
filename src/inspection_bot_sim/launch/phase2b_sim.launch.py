"""
Phase 2B-1-FIX-C: Gazebo with world-included robot model (SDF + lidar sensor).

Robot model is loaded at world startup via <include> — sensor activates reliably.
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc_share = FindPackageShare("inspection_bot_description").find("inspection_bot_description")
    sim_share  = FindPackageShare("inspection_bot_sim").find("inspection_bot_sim")
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # Robot description for TF (URDF model for robot_state_publisher)
    xacro_file = os.path.join(desc_share, "urdf", "robot.xacro")
    robot_desc = {"robot_description": ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]), value_type=str)}

    # Model path for Gazebo to find model://inspection_bot
    models_path = os.path.join(sim_share, "models")
    # Also include home models for fallback
    home_models = os.path.expanduser("~/.ignition/gazebo/models")
    gz_model_path = f"{models_path}:{home_models}"

    world_path = os.path.join(sim_share, "worlds", "phase2b_simple.sdf")

    # Gazebo with model path set
    set_model_path = SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", gz_model_path)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ]),
        launch_arguments={"gz_args": f"-r {world_path}"}.items(),
    )

    # TF from URDF
    rsp = Node(package="robot_state_publisher", executable="robot_state_publisher",
               output="both", parameters=[robot_desc, {"use_sim_time": use_sim_time}])

    # Controllers (robot spawns via world include, controllers loaded after)
    jsp = Node(package="controller_manager", executable="spawner",
               arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
               parameters=[{"use_sim_time": use_sim_time}])
    fs = Node(package="controller_manager", executable="spawner",
              arguments=["front_steering_controller", "-c", "/controller_manager"],
              parameters=[{"use_sim_time": use_sim_time}])
    dr = Node(package="controller_manager", executable="spawner",
              arguments=["drive_controller", "-c", "/controller_manager"],
              parameters=[{"use_sim_time": use_sim_time}])
    delay_ctrl = TimerAction(period=8.0, actions=[jsp, fs, dr])

    # Adapter
    adapter = Node(package="inspection_bot_description", executable="gazebo_cmd_vel_adapter",
                   name="gazebo_cmd_vel_adapter", output="screen",
                   parameters=[{"use_sim_time": True, "wheelbase": 0.460, "track_width": 0.476,
                                "wheel_radius": 0.076, "max_speed_mps": 0.10, "max_reverse_speed_mps": 0.05,
                                "max_angular_speed_radps": 0.30, "max_steering_angle_rad": 0.785,
                                "odom_frame": "odom", "base_frame": "base_link"}])
    delay_adapter = TimerAction(period=10.0, actions=[adapter])

    # /scan bridge (GZ -> ROS2 /scan_raw)
    bridge = Node(package="ros_gz_bridge", executable="parameter_bridge", name="bridge_scan",
                  output="screen",
                  arguments=["/scan_raw@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan"],
                  parameters=[{"use_sim_time": use_sim_time}])

    # Frame normalizer: /scan_raw -> /scan (frame_id=lidar_link)
    normalizer = Node(package="inspection_bot_sim", executable="scan_frame_normalizer",
                      name="scan_frame_normalizer", output="screen",
                      parameters=[{"use_sim_time": use_sim_time}])

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        set_model_path,
        gz_sim, rsp, delay_ctrl, delay_adapter, bridge, normalizer,
    ])
