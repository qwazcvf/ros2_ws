# 建图操作流程

## 一、在线采集

```bash
# 终端1：启动雷达
cd ~/ros2_ws && ./start_lidar.sh

# 终端2：启动 FAST-LIO SLAM
cd ~/ros2_ws && ./start_slam.sh

# 终端3：保存点云（每2秒更新 latest.pcd，Ctrl+C 时存 final.pcd）
cd ~/ros2_ws && python3 save_pcd.py
```

推着车走一圈，覆盖要建图的区域。走完后在终端3按 Ctrl+C。

输出：
- `~/ros2_ws/maps/latest.pcd` — 实时更新的快照
- `~/ros2_ws/maps/final.pcd` — 最终完整点云

## 二、离线转 2D 地图

```bash
cd ~/ros2_ws
python3 pcd_to_2d_map.py maps/final.pcd --output 2D_map
```

输出：
- `~/ros2_ws/maps/2D_map.pgm` — Nav2 可加载的占据栅格
- `~/ros2_ws/maps/2D_map.yaml` — 地图元数据
- `~/ros2_ws/maps/2D_map_debug.png` — 验证用图

## 三、调参

编辑 `pcd_to_2d_map.py` 开头：

| 参数 | 作用 |
|------|------|
| `GROUND_PERCENTILE` | 地面百分位，越小越保守 |
| `GROUND_TOLERANCE` | 多高算地面 |
| `OBSTACLE_MIN_H` | 多高算障碍 |
| `OBSTACLE_MAX_H` | 多高以上忽略 |
| `DILATE_PIXELS` | 墙体膨胀 |
| `MIN_COMPONENT` | 小噪点过滤 |

改完不用编译，直接跑 `python3 pcd_to_2d_map.py`。
