# unitree_lidar_ros2

This is a ROS2 package using open source C++ driver for Unitree Lidar L2.

这是一个使用开源 C++ 驱动程序的 ROS2 软件包，用于 Unitree Lidar L2 激光雷达。

需搭配此 [开源驱动](https://github.com/discodyer/unilidar_driver) 使用。

---

## **⚠️ 免责声明 / Disclaimer**

**本仓库代码仅供学习和研究使用。**

- 原官方仓库地址：[仓库地址](https://github.com/unitreerobotics/unilidar_sdk2)
- 本驱动为非官方实现，未经设备制造商授权
- 使用本驱动程序可能导致设备损坏、保修失效或其他不可预见的问题
- **使用者需自行承担所有风险和后果，开发者不对任何损失负责**
- 建议在非生产环境中谨慎测试

---

## 编译说明

### 系统要求

- Linux / Windows
- ROS2 humble

### 编译步骤

```bash
# Creating colcon workspace
mkdir -p ~/unilidar_ws/src
cd ~/unilidar_ws/src

# Cloning repository
git clone https://github.com/discodyer/unilidar_driver.git --recurse-submodules
git clone https://github.com/discodyer/unitree_lidar_ros2.git

# Compilation
cd ~/unilidar_ws
colcon build
```

## Using package

Run:
```bash
source ~/unilidar_ws/install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

## license

The origin repository was created by Unitree Robotics.

https://github.com/unitreerobotics/unilidar_sdk2

BSD 3-Clause License
