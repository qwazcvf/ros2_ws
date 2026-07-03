# Inspection Bot Description — Phase 2A

ROS 2 Humble package for **Gazebo simulation** of a 4-wheel front-steering 4WD inspection robot.

**Phase 2A scope:** Low-speed Ackermann-like simulation with unified `/cmd_vel` interface.
No Nav2, no real LIDAR, no real MCU, no 4-wheel independent steering.

## ⚠️ Important Constraints (Phase 2A)

- **Do NOT run `nano_base_bridge simulation_mode=true` alongside Gazebo.**
  This causes `/odom` and `odom → base_link` TF publication conflicts.
- This phase does **NOT** do: Nav2, real LIDAR, real MCU, autonomous driving,
  4-wheel independent steering, crab mode, or spot-rotate.
- `/odom` published by `gazebo_cmd_vel_adapter` is **simulation test odometry** —
  it is NOT real localization, NOT LIO/SLAM odometry. It uses simple dead-reckoning
  integration inside the adapter for Phase 2A interface testing only.
- `/scan` is **not enabled** in this phase. `lidar_link` exists in the URDF but
  no virtual laser scan is published. Real Unitree LIDAR driver is NOT used here.

## Interface Architecture (Phase 2A)

```
┌──────────────────────────────────────────────────────────┐
│  keyboard_control.py   or   test publisher               │
│         ↓ /cmd_vel (geometry_msgs/Twist)                 │
│         │  linear.x  only (forward/reverse)              │
│         │  angular.z only (left/right turn)              │
│         │  all other fields ignored                      │
│                                                          │
│  gazebo_cmd_vel_adapter                                  │
│    ├── Ackermann front-steering calculation              │
│    ├── /front_steering_controller/commands [fl, fr]      │
│    ├── /drive_controller/commands [fl, fr, rl, rr]       │
│    ├── /odom (frame: odom, child: base_link)             │
│    └── TF: odom → base_link                              │
│         ↓                                                │
│  ros2_control (inside Gazebo)                            │
│    ├── front_steering_controller (position, active)      │
│    ├── drive_controller (velocity, active)               │
│    └── joint_state_broadcaster (active)                  │
│         ↓                                                │
│  Simulated vehicle in Ignition Gazebo                    │
└──────────────────────────────────────────────────────────┘
```

**External control uses ONLY `/cmd_vel`.** Controller command topics are internal
Gazebo interfaces. Do NOT publish directly to:
- `/front_steering_controller/commands`
- `/drive_controller/commands`
- `/steering_controller/commands` (deprecated in Phase 2A)
- `/rear_steering_controller/commands` (not configured in Phase 2A)

## /odom Status (Phase 2A)

| Item | Value |
|---|---|
| Publisher | `gazebo_cmd_vel_adapter` (sole publisher) |
| frame_id | `odom` |
| child_frame_id | `base_link` |
| Source | Simple dead-reckoning integration inside adapter |
| Purpose | Phase 2A simulation interface testing |
| NOT | Real localization / LIO / SLAM |

## /scan Status (Phase 2A)

`lidar_link` exists in the URDF at `(0.36101, -0.000993, 0.35253)`.
Virtual `/scan` is **not enabled**. Real Unitree LIDAR driver is NOT used in this phase.

## TF Tree

```
odom → base_link (from gazebo_cmd_vel_adapter)
base_link
 ├── fl_steering_link (steering joint: continuous, axis Z)
 │    └── fl_wheel_link (wheel joint: continuous, axis Y)
 ├── fr_steering_link (steering joint: continuous, axis Z)
 │    └── fr_wheel_link (wheel joint: continuous, axis Y)
 ├── rl_steering_link (steering joint: continuous, axis Z) [Phase 2A: locked]
 │    └── rl_wheel_link (wheel joint: continuous, axis Y)
 ├── rr_steering_link (steering joint: continuous, axis Z) [Phase 2A: locked]
 │    └── rr_wheel_link (wheel joint: continuous, axis Y)
 ├── lidar_link (fixed)
 └── camera_link (fixed)
```

## Joints

| Joint | Type | Parent | Child | Axis | Phase 2A |
|---|---|---|---|---|---|
| `fl_steering_joint` | continuous | base_link | fl_steering_link | Z | **position-controlled** |
| `fr_steering_joint` | continuous | base_link | fr_steering_link | Z | **position-controlled** |
| `rl_steering_joint` | continuous | base_link | rl_steering_link | Z | **state-only (locked)** |
| `rr_steering_joint` | continuous | base_link | rr_steering_link | Z | **state-only (locked)** |
| `fl_wheel_joint` | continuous | fl_steering_link | fl_wheel_link | Y | velocity-controlled |
| `fr_wheel_joint` | continuous | fr_steering_link | fr_wheel_link | Y | velocity-controlled |
| `rl_wheel_joint` | continuous | rl_steering_link | rl_wheel_link | Y | velocity-controlled |
| `rr_wheel_joint` | continuous | rr_steering_link | rr_wheel_link | Y | velocity-controlled |
| `lidar_joint` | fixed | base_link | lidar_link | — | — |
| `camera_joint` | fixed | base_link | camera_link | — | — |

## Package Structure

```
inspection_bot_description/
├── config/
│   └── controllers.yaml              # Phase 2A: front_steering + drive
├── inspection_bot_description/
│   ├── __init__.py
│   ├── keyboard_control.py           # /cmd_vel keyboard (Phase 2A)
│   ├── gazebo_cmd_vel_adapter.py     # /cmd_vel → controller + /odom + TF
│   └── static_joint_state_publisher.py
├── launch/
│   ├── view_model.launch.py          # RViz only
│   ├── gz_sim.launch.py              # Ignition Gazebo Fortress (primary)
│   └── gazebo.launch.py              # Classic Gazebo 11 (Jetson: not available)
├── rviz/display.rviz
├── urdf/
│   ├── robot.xacro                   # Phase 2A xacro
│   ├── robot_old_from_sw.urdf        # SW-exported URDF (backup)
│   └── robot.csv                     # SW-exported parameters
├── worlds/empty.world
├── package.xml
└── setup.py
```

## Installation (Jetson ARM64)

```bash
# Add OSRF repo
sudo sh -c 'echo "deb https://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main" > /etc/apt/sources.list.d/gazebo-stable.list'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys D2486D2DD83DB69272AFE98867170598AF249743
sudo apt update

# Install Ignition Gazebo + ros2_control
sudo apt install ros-humble-ros-gz-sim ros-humble-gz-ros2-control
sudo apt install ros-humble-controller-manager ros-humble-joint-state-broadcaster
sudo apt install ros-humble-position-controllers ros-humble-velocity-controllers
```

```bash
cd ~/ros2_ws
colcon build --packages-select inspection_bot_description --symlink-install
source install/setup.bash
```

## Quick Start

### Terminal 1: Gazebo Simulation

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch inspection_bot_description gz_sim.launch.py
```

Wait ~10s for Gazebo + controllers + adapter.

### Terminal 2: Keyboard Control

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run inspection_bot_description keyboard_control
```

| Key | Action |
|---|---|
| W / S | Forward / Reverse |
| A / D | Turn Left / Right |
| SPACE / X | Stop |
| Q / E / Z / C | Disabled |
| ESC | Quit |

### Manual /cmd_vel Commands

```bash
# Forward (0.08 m/s)
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08}, angular: {z: 0.0}}"

# Reverse (-0.04 m/s)
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: -0.04}, angular: {z: 0.0}}"

# Left turn (0.08 m/s + 0.30 rad/s)
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08}, angular: {z: 0.30}}"

# Right turn (0.08 m/s + -0.30 rad/s)
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08}, angular: {z: -0.30}}"

# Pure angular.z — vehicle does NOT move or steer
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.30}}"

# Stop
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

## Controller Architecture (Phase 2A)

```
controller_manager (inside Gazebo plugin)
 ├── joint_state_broadcaster   → /joint_states (8 joints)
 ├── front_steering_controller ← /front_steering_controller/commands [fl, fr]
 └── drive_controller          ← /drive_controller/commands [fl, fr, rl, rr]

Hardware: ign_ros2_control/IgnitionSystem (libgz_ros2_control-system.so)
```

## Adapter Parameters

| Parameter | Default | Description |
|---|---|---|
| `wheelbase` | 0.460 | Front-rear axle distance (m) |
| `track_width` | 0.476 | Left-right wheel distance (m) |
| `wheel_radius` | 0.076 | Wheel radius (m) |
| `max_speed_mps` | 0.10 | Max forward speed (m/s) |
| `max_reverse_speed_mps` | 0.05 | Max reverse speed (m/s) |
| `max_angular_speed_radps` | 0.30 | Max angular speed (rad/s) |
| `max_steering_angle_rad` | 0.60 | Max front steering angle (rad) |
| `cmd_timeout_sec` | 0.5 | /cmd_vel timeout (s) — stops if no msg |
| `odom_rate_hz` | 30.0 | Odom publish rate (Hz) |

## Gazebo Version

Jetson ARM64 → **Ignition Gazebo Fortress** (`ros_gz_sim`). Classic Gazebo 11 is not available.

## Geometry

| Part | Shape | Dimensions |
|---|---|---|
| Chassis board | box | 0.806 × 0.607 × 0.03 m |
| Wheel | cylinder | r=0.076 m, w=0.04 m |
| LiDAR | cylinder | r=0.035 m, h=0.06 m |
| Camera | box | 0.06 × 0.035 × 0.035 m |

### Key Positions

| Feature | X | Y | Z |
|---|---|---|---|
| Front axle | 0.2316 | — | — |
| Rear axle | -0.2284 | — | — |
| Left wheels | — | 0.238 | — |
| Right wheels | — | -0.238 | — |
| Steering joint Z | — | — | -0.055 |
| Wheel center Z | — | — | -0.179 |
| LiDAR | 0.36101 | -0.000993 | 0.35253 |
| Camera | 0.4056 | 0 | 0.21 |

## Debugging

```bash
source /opt/ros/humble/setup.bash && source ~/ros2_ws/install/setup.bash

# Controllers
ros2 control list_controllers

# Joint states
ros2 topic echo /joint_states --once

# /cmd_vel subscribers
ros2 topic info /cmd_vel -v

# /odom publisher
ros2 topic info /odom -v

# TF
ros2 run tf2_ros tf2_echo odom base_link

# Verify URDF
xacro src/inspection_bot_description/urdf/robot.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf

# RViz only (no Gazebo)
ros2 launch inspection_bot_description view_model.launch.py
```
