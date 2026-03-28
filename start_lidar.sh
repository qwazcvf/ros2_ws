#!/bin/bash

# 1. 检查雷达是否正常连接 (应输出 /dev/ttyACM0)
echo "Checking for LiDAR connection..."
if [ ! -e /dev/ttyACM0 ]; then
  echo "Error: LiDAR not found at /dev/ttyACM0!"
  exit 1
fi
echo "LiDAR found at /dev/ttyACM0."

# 2. 赋予串口超级权限 (会要求输入 jetson 的开机密码)
echo "Setting permissions for /dev/ttyACM0..."
sudo chmod 777 /dev/ttyACM0

# 3. 进入工作空间并刷新环境变量
echo "Sourcing workspace environment..."
source /opt/ros/humble/setup.bash
source install/setup.bash

# 4. 点火启动 ROS 2 节点
echo "Launching unitree_lidar_ros2..."
ros2 launch unitree_lidar_ros2 launch.py
