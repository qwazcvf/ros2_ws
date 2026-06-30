# Unitree L2 雷达使用说明（UDP 网口模式）

> 最后更新：2026-06-30  
> 连接方式：**网线（UDP）**，不再使用串口

---

## 一、硬件连接

| 接口 | 连接对象 | 说明 |
|------|----------|------|
| 网线 | Jetson `enP8p1s0` ↔ 雷达网口 | 必须插，数据传输 |
| USB 串口 | 不插 | 已切为 UDP 模式，不需要了 |
| 电源 | 雷达供电 | 必须插 |

---

## 二、每次开机启动雷达

### 1. 给 Jetson 网口配 IP（每次开机做一次）

```bash
sudo ip addr add 192.168.1.2/24 dev enP8p1s0
```

> ⚠️ 目前是临时配置，重启后需重新执行。永久配置见第五节。

### 2. 启动雷达 ROS2 节点

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

点云话题：`/unilidar/cloud`（约 5000 点/帧）  
IMU 话题：`/unilidar/imu`

### 3. 启动 FAST-LIO 建图（另一个终端）

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch fast_lio mapping.launch.py config_file:=unilidar_l2.yaml
```

---

## 三、网络参数速查

| 参数 | 值 | 说明 |
|------|------|------|
| 雷达 IP | `192.168.1.62` | 出厂默认，切勿改动 |
| 雷达端口 | `6101` | UDP 数据端口 |
| Jetson IP | `192.168.1.2` | 需手动配置 |
| Jetson 端口 | `6201` | 本地接收端口 |
| Jetson 网口 | `enP8p1s0` | 有线网卡名 |

---

## 四、本次修改说明

### 修改了 4 个文件

| 文件 | 改动内容 |
|------|----------|
| `unilidar_sdk2/.../launch.py` | `initialize_type` 1→2（串口切网口），IP 修正 |
| `unilidar_sdk2/.../unitree_lidar_ros2.h` | 默认 IP 修正 + 添加 `startLidarRotation/resetLidar` |
| `unilidar_fastlio_ros2-ros2/src/preprocess.h` | LID_TYPE 枚举增加 `UNITREE = 5` |
| `unilidar_fastlio_ros2-ros2/src/preprocess.cpp` | `case UNITREE:` 走 velodyne_handler |

### 为什么改 preprocess？

之前 `lidar_type: 5` 不存在，走 `default_handler` 丢失了每点的 `time` 和 `ring`，导致 FAST-LIO 运动补偿失效——点云"飞了"。现在正确提取时间戳。

### 硬件操作历史

1. 串口连雷达 → `setLidarIpAddressConfig` + `setLidarWorkMode(0)` 配好 IP 和 UDP 模式
2. 拔掉串口线 → 断电重启雷达
3. 网线直连 → Jetson IP 设为 `192.168.1.2`

---

## 五、永久 IP 配置（可选）

编辑 netplan 或添加到启动脚本：

```bash
# 方法1：编辑 /etc/rc.local（在 exit 0 前添加）
sudo ip addr add 192.168.1.2/24 dev enP8p1s0
```
