# 航空部装厂房巡检机器人 - 3D 雷达感知与建图模块

本项目为基于四向四驱底盘结构的巡检机器人提供核心的 3D 空间感知与建图能力。针对边缘计算平台（Jetson Nano / ARM 架构）进行了深度适配与性能优化。

本模块融合了 **Unitree L2 激光雷达**的高频点云数据与底层 IMU 数据，并采用定制版 **FAST-LIO** (Fast LiDAR-Inertial Odometry) 算法实现低延迟、高精度的实时三维建图。

## 🛠️ 硬件与环境配置
* **计算平台**: Nvidia Jetson Nano (ARM 架构)
* **操作系统**: Ubuntu 22.04 + ROS 2 (Humble)
* **核心传感器**: 宇树 Unitree L2 激光雷达 (含内置 IMU)
* **通信波特率**: 4000000 bps (已在底层 SDK 修复超时断连 Bug)

> **⚠️ 硬件避坑级警告 (每次开机必看)**
> 1. **供电与带宽**：雷达的 USB 线 **必须** 插在 Jetson Nano 的 **蓝色 USB 3.0 接口** 上！若误插黑色 USB 2.0 接口，必报 `Serial port timeout` 错误！
> 2. **确认设备名**：雷达上电后，请确保系统已将其识别为 `/dev/ttyACM0`。

## 📂 核心代码结构
工作空间 `ros2_ws/src` 下包含以下核心功能包：
* `unitree_lidar_ros2`: 宇树 L2 雷达 ROS 2 原生驱动（已过滤 ROS 1 冲突包）。
* `unilidar_fastlio_ros2-ros2`: 宇树官方定制版 FAST-LIO 紧耦合建图算法，开箱即用，无需修改外部依赖。

## 🚀 极速启动指南 (Quick Start)

为了最大程度简化部署流程，本项目已将复杂的节点配置与环境配置封装为两个一键启动脚本。只需简单的两步，即可在 Jetson Nano 上跑通雷达与 3D 建图：

**⚠️ 首次克隆本仓库后，请先赋予脚本可执行权限（仅需执行一次）：**
```bash
cd ~/ros2_ws
chmod +x start_lidar.sh start_slam.sh

**⚠️ 如果显示Serial time not：**
find ~/ros2_ws/src/unilidar_sdk2 -type f -executable | grep -iE "bin/.*(test|serial|unilidar)"

/home/jetson/ros2_ws/src/unilidar_sdk2/unitree_lidar_sdk/bin/example_lidar_serial


1. 打开第一个终端启动雷达驱动
Bash

cd ~/ros2_ws
./start_lidar.sh

2. 打开第二个终端开启激光 SLAM 建图
Bash

cd ~/ros2_ws
./start_slam.sh

3.打开第三个终端开启摄像头画面
cd ~/ros2_ws
./start_camera.sh
4.保存图
cd ~/ros2_ws
python3 map_builder.py
