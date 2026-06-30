# Jetson Orin Nano + Unitree L2 激光雷达 + FAST-LIO 建图

## 硬件

- **Jetson Orin Nano** (ARM64, Ubuntu 22.04, ROS2 Humble)
- **Unitree L2 激光雷达** (18线, 360°机械旋转)
- **连接方式**: 网线直连 (UDP), 不再使用 USB 串口

## 网络配置

| 设备 | IP | 端口 |
|------|------|------|
| 雷达 (Unitree L2) | `192.168.1.62` | `6101` |
| Jetson 网口 (`enP8p1s0`) | `192.168.1.2` | `6201` |

## 建图流程

### 第一步：在线采集点云

```bash
# 终端1: 启动雷达驱动
cd ~/ros2_ws && ./start_lidar.sh

# 终端2: 启动 FAST-LIO SLAM
cd ~/ros2_ws && ./start_slam.sh

# 终端3: 保存点云 (每2秒存 latest.pcd, Ctrl+C 存 final.pcd)
cd ~/ros2_ws && python3 save_pcd.py
```

推车走一圈覆盖建图区域, 完成后在终端3按 `Ctrl+C`。

### 第二步：离线生成 2D 地图

```bash
cd ~/ros2_ws
python3 pcd_to_2d_map.py maps/final.pcd --output 2D_map
```

输出:
- `maps/2D_map.pgm` — Nav2 可加载的占据栅格地图
- `maps/2D_map.yaml` — 地图元数据
- `maps/2D_map_debug.png` — 调参验证用图 (红=障碍, 绿=地面)

## 调参

编辑 `pcd_to_2d_map.py` 头部参数:

```python
GROUND_PERCENTILE = 10    # 地面百分位, 越小越保守
GROUND_TOLERANCE = 0.10   # 多高算地面 (m)
OBSTACLE_MIN_H = 0.10     # 最低障碍高度 (m)
OBSTACLE_MAX_H = 2.20     # 最高障碍高度 (m)
DILATE_PIXELS = 1         # 墙体膨胀像素数
MIN_COMPONENT = 8         # 小于此格数的小连通域删除
```

## 本次更新 (2026-06-30)

### 雷达: 串口 → UDP 网口

- **动机**: 串口带宽瓶颈, 偶尔丢数据导致 FAST-LIO 点云"飞了"
- **改动文件**:
  - `src/unilidar_sdk2/.../launch.py`: `initialize_type` 1→2, IP 修正
  - `src/unilidar_sdk2/.../unitree_lidar_ros2.h`: 默认 IP 修正 + 启动时自动复位雷达
  - `start_lidar.sh`: 去掉串口检查, 改为自动配置网口 IP

### FAST-LIO: 修复 lidar_type 时间戳丢失

- **问题**: `lidar_type: 5` 在枚举中不存在, 走到 `default_handler`, 每个点的 `time` 和 `ring` 全丢了, 运动补偿失效
- **改动**: `src/unilidar_fastlio_ros2-ros2/src/preprocess.h/cpp` 增加 `UNITREE = 5`, 走 `velodyne_handler` 正确提取每点时间戳

### 建图: 简化为离线 PCD → 2D

- **废弃**: `map_builder.py`, `start_map_builder.sh`, `fastlio_2d_map_builder`, `start_octomap.launch.py`
- **新方案**: `save_pcd.py` (在线存 PCD) + `pcd_to_2d_map.py` (离线转 2D)
- **优势**: 调参不用重新跑 SLAM, 同一份 PCD 可以反复尝试不同参数

## 文件说明

| 文件 | 用途 |
|------|------|
| `start_lidar.sh` | 一键启动雷达 (自动配 IP) |
| `start_slam.sh` | 一键启动 FAST-LIO |
| `save_pcd.py` | 在线累积点云并定期保存 PCD |
| `pcd_to_2d_map.py` | 离线 PCD → 2D PGM/YAML |
| `RADAR_README.md` | 雷达详细说明 (含故障排查) |
| `HOWTO_MAP.md` | 建图操作速查 |

## 文件结构

```
~/ros2_ws/
├── src/
│   ├── unilidar_sdk2/          # Unitree LiDAR SDK + ROS2 wrapper
│   └── unilidar_fastlio_ros2-ros2/  # FAST-LIO 3D SLAM
├── start_lidar.sh
├── start_slam.sh
├── save_pcd.py
├── pcd_to_2d_map.py
├── maps/                       # 输出地图 (不入 git)
│   ├── final.pcd
│   ├── 2D_map.pgm
│   └── 2D_map.yaml
├── RADAR_README.md
└── HOWTO_MAP.md
```
