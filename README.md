# 宇树 L2 激光雷达 (Jetson Nano 专版)

本项目包含在 ARM 架构的 Jetson Nano 上成功运行的宇树 L2 雷达 ROS 2 驱动代码。
已针对 4000000 波特率和底层 timeout 问题进行了深度适配。

## ⚠️ 硬件避坑指南 (每次点火前必看)
1. **供电与带宽**：雷达的 USB 线 **必须** 插在 Jetson Nano 的 **蓝色 USB 3.0 接口** 上！插黑口必报 `timeout` 错误。
2. **确认设备**：确保雷达已被识别为 `/dev/ttyACM0`。

## 🚀 启动指令 (标准四步曲)

打开终端，依次执行以下命令：

```bash
# 1. 检查雷达是否正常连接 (应输出 /dev/ttyACM0)
ls /dev/ttyACM*

# 2. 赋予串口超级权限 (会要求输入 jetson 的开机密码)
sudo chmod 777 /dev/ttyACM0

# 3. 进入工作空间并刷新环境变量
cd ~/ros2_ws
source install/setup.bash

# 4. 点火启动 ROS 2 节点与 RViz
ros2 launch unitree_lidar_ros2 launch.py

## 🚀 建图启动指令 (另一个终端)
cd ~/ros2_ws
source install/setup.bash
ros2 launch fast_lio mapping.launch.py

