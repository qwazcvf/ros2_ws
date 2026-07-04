# Inspection Bot Sim — Phase 2B-1

Gazebo simulation package: factory world, virtual 2D `/scan`, and RViz config.

## What This Package Does

- Launches Ignition Gazebo with a simple factory-world scene
- Spawns the inspection bot robot model
- Provides a virtual 2D LaserScan `/scan` for Nav2 costmap testing
- Provides RViz config for visualization

## What `/scan` Is (and Is Not)

- **IS**: Gazebo virtual 2D LaserScan, 360 degrees, 10 Hz, range 0.1–15 m
- **IS NOT**: Real Unitree L2 3D lidar
- Real Unitree L2 + FAST-LIO will be added in Phase 3A separately
- `/scan` is used now to quickly verify the Nav2 costmap perception pipeline

## Quick Start

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 launch inspection_bot_sim phase2b_sim.launch.py
```

## Check `/scan`

```bash
ros2 topic list | grep scan
ros2 topic info /scan -v
ros2 topic echo /scan --once
```

## Check TF

```bash
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 run tf2_ros tf2_echo odom base_link
```

## RViz

```bash
rviz2 -d $(ros2 pkg prefix inspection_bot_sim)/share/inspection_bot_sim/rviz/phase2b_scan.rviz
```

Fixed Frame: `odom`. Displays: RobotModel, TF, LaserScan, Odometry.

## Motion Test

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08}, angular: {z: 0.0}}"
```

Observe `/scan` ranges change as the robot moves near obstacles.

## Important Constraints

- Do NOT run `nano_base_bridge simulation_mode=true` with Gazebo
- `/odom` is published by `gazebo_cmd_vel_adapter` (sim test odometry, NOT real localization)
- Real car `/odom` will come from FAST-LIO / LIO / fused odometry in Phase 3A
- For real-car RViz: point cloud display depends on correct `base_link -> lidar_link` TF
  and LIO/odom/map frame chain with correct `frame_id` in PointCloud2

## Phase Status

| Phase | Status |
|---|---|
| Phase 2A | PASS — /cmd_vel, /odom, TF, front-steering |
| Phase 2B-1 | Current — virtual /scan, factory world |
| Phase 2B-2 | Future — 3D PointCloud2 virtual lidar |
| Phase 3A | Future — real Unitree L2 + FAST-LIO |

## World

`phase2b_simple.sdf`: flat ground, 4 walls, 2 shelf racks, 2 cargo boxes, 1 scaffold pillar.
Modeled after an aviation assembly factory interior.
