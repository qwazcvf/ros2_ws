#!/bin/bash

# 进入工作空间并刷新环境变量
echo "Sourcing workspace environment..."
source /opt/ros/humble/setup.bash
source install/setup.bash

# 启动 SLAM
echo "Launching fast_lio SLAM..."
ros2 launch fast_lio mapping.launch.py
