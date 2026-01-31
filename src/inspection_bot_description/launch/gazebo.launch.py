import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    package_name = 'inspection_bot_description'

    # 1. 解析 URDF 文件
    pkg_path = os.path.join(get_package_share_directory(package_name))
    xacro_file = os.path.join(pkg_path, 'urdf', 'robot.urdf')
    # 处理 xacro (虽然你的文件叫 urdf，但用 xacro 解析器更稳健)
    robot_description_config = xacro.process_file(xacro_file)
    params = {'robot_description': robot_description_config.toxml()}

    # 2. 节点：机器人状态发布 (发布 TF)
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    # 3. 节点：启动 Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
    )

    # 4. 节点：在 Gazebo 中生成机器人
    # 注意：-z 0.3 让机器人出生在半空，落地更稳
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_bot', '-z', '0.3'],
        output='screen'
    )

    # ================= 🆕 控制器加载部分 =================

    # 5. 加载关节状态广播器 (Joint State Broadcaster)
    # 它的作用是把关节角度发给 ROS，这样 RViz 里的轮子才会转
    load_joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    # 6. 加载前轮转向控制器
    load_front_steering = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["front_steering_controller"],
        output="screen",
    )

    # 7. 加载后轮转向控制器
    load_rear_steering = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["rear_steering_controller"],
        output="screen",
    )

    # 8. 加载驱动控制器 (控制车轮速度)
    load_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["drive_controller"],
        output="screen",
    )

    # ====================================================

    return LaunchDescription([
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        
        # 必须等机器人生成 (spawn) 完之后，再加载控制器
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[
                    load_joint_state_broadcaster,
                    load_front_steering,
                    load_rear_steering,
                    load_drive_controller,
                ],
            )
        ),
    ])