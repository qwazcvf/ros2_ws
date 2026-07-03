# Inspection Bot Description — Front-Steering 4WD

ROS 2 Humble robot description package for a **4-wheel front-steering 4WD** inspection robot.

## Architecture

```
base_link (chassis board 0.806×0.607×0.03 + wireframe acrylic shell)
 ├── fl_steering_joint → fl_steering_link → fl_wheel_joint → fl_wheel_link
 ├── fr_steering_joint → fr_steering_link → fr_wheel_joint → fr_wheel_link
 ├── rl_steering_joint → rl_steering_link → rl_wheel_joint → rl_wheel_link
 ├── rr_steering_joint → rr_steering_link → rr_wheel_joint → rr_wheel_link
 ├── lidar_joint  → lidar_link
 └── camera_joint → camera_link
```

## TF Tree

```
base_link
 ├── fl_steering_link (steering joint: continuous, axis Z)
 │    └── fl_wheel_link (wheel joint: continuous, axis Y)
 ├── fr_steering_link (steering joint: continuous, axis Z)
 │    └── fr_wheel_link (wheel joint: continuous, axis Y)
 ├── rl_steering_link (steering joint: continuous, axis Z)
 │    └── rl_wheel_link (wheel joint: continuous, axis Y)
 ├── rr_steering_link (steering joint: continuous, axis Z)
 │    └── rr_wheel_link (wheel joint: continuous, axis Y)
 ├── lidar_link (fixed)
 └── camera_link (fixed)
```

## Joints

| Joint | Type | Parent | Child | Axis | Control |
|---|---|---|---|---|---|
| `fl_steering_joint` | continuous | base_link | fl_steering_link | Z | position |
| `fr_steering_joint` | continuous | base_link | fr_steering_link | Z | position |
| `rl_steering_joint` | continuous | base_link | rl_steering_link | Z | position |
| `rr_steering_joint` | continuous | base_link | rr_steering_link | Z | position |
| `fl_wheel_joint` | continuous | fl_steering_link | fl_wheel_link | Y | velocity |
| `fr_wheel_joint` | continuous | fr_steering_link | fr_wheel_link | Y | velocity |
| `rl_wheel_joint` | continuous | rl_steering_link | rl_wheel_link | Y | velocity |
| `rr_wheel_joint` | continuous | rr_steering_link | rr_wheel_link | Y | velocity |
| `lidar_joint` | fixed | base_link | lidar_link | — | — |
| `camera_joint` | fixed | base_link | camera_link | — | — |

## Control Mode

**Front-steering 4WD with Ackermann geometry:**
- Front wheels (fl, fr): steer via Ackermann angles
- Rear wheels (rl, rr): fixed straight
- All four wheels: driven at same speed

## Package Structure

```
inspection_bot_description/
├── config/
│   └── controllers.yaml              # ros2_control configuration
├── inspection_bot_description/
│   ├── __init__.py
│   ├── keyboard_control.py           # keyboard controller (front-steering 4WD)
│   └── static_joint_state_publisher.py
├── launch/
│   ├── view_model.launch.py          # RViz only
│   ├── gz_sim.launch.py              # Ignition Gazebo Fortress (primary)
│   └── gazebo.launch.py              # Classic Gazebo 11 (Jetson: not available)
├── meshes/                           # STL meshes from SW export (unused)
├── rviz/
│   └── display.rviz                  # RViz configuration
├── urdf/
│   ├── robot.xacro                   # Main xacro with corner macro
│   ├── robot_old_from_sw.urdf        # Original SW-exported URDF (backup)
│   ├── robot.urdf                    # Old URDF (kept for reference)
│   └── robot.csv                     # SW-exported parameters
├── worlds/
│   └── empty.world                   # Empty Gazebo world
├── package.xml
├── setup.py
└── setup.cfg
```

## Installation (Jetson ARM64)

### Prerequisites

```bash
# ROS 2 Humble should already be at /opt/ros/humble

# Add OSRF repo (for updated libignition-sensors6)
sudo sh -c 'echo "deb https://packages.osrfoundation.org/gazebo/ubuntu-stable jammy main" > /etc/apt/sources.list.d/gazebo-stable.list'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys D2486D2DD83DB69272AFE98867170598AF249743
sudo apt update

# Install Ignition Gazebo + ros2_control
sudo apt install ros-humble-ros-gz-sim ros-humble-gz-ros2-control
sudo apt install ros-humble-controller-manager ros-humble-joint-state-broadcaster
sudo apt install ros-humble-position-controllers ros-humble-velocity-controllers
```

### Build

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

Wait ~10 seconds until Gazebo window opens and robot spawns.

### Terminal 2: Keyboard Control

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run inspection_bot_description keyboard_control
```

| Key | Action |
|---|---|
| W / S | Forward / Reverse (all 4 wheels) |
| A / D | Front steering Left / Right (Ackermann) |
| SPACE / X | Stop + center steering |
| Q / E / Z / C | Disabled |
| ESC | Quit |

### Terminal 3 (optional): Monitor

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# Check controllers
ros2 control list_controllers

# Watch joint states
ros2 topic echo /joint_states --once
```

### RViz Display (no simulator)

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch inspection_bot_description view_model.launch.py
```

### Verify URDF

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
xacro src/inspection_bot_description/urdf/robot.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf
```

### Manual Joint Commands

```bash
# Steer front wheels to 30 degrees (0.524 rad)
ros2 topic pub --once /steering_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [0.524, 0.524, 0.0, 0.0]}"

# Drive all wheels at 5 rad/s
ros2 topic pub --once /drive_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [5.0, 5.0, 5.0, 5.0]}"
```

## Controller Architecture

```
controller_manager (inside Gazebo plugin)
 ├── joint_state_broadcaster  → /joint_states (8 joints)
 ├── steering_controller      ← /steering_controller/commands [fl, fr, rl, rr] position
 └── drive_controller         ← /drive_controller/commands [fl, fr, rl, rr] velocity

Hardware: ign_ros2_control/IgnitionSystem (via libgz_ros2_control-system.so)
```

## Gazebo Version

This Jetson ARM64 platform uses **Ignition Gazebo Fortress** (`ros_gz_sim`).
Classic Gazebo 11 is not available on ARM64.

- Hardware plugin: `ign_ros2_control/IgnitionSystem`
- Gazebo plugin: `libgz_ros2_control-system.so`
- Controller manager runs **inside** Gazebo (no standalone ros2_control_node)

## Geometry

| Part | Shape | Dimensions |
|---|---|---|
| Chassis board | box | 0.806 × 0.607 × 0.03 m |
| Wheel | cylinder | r=0.076 m (76mm), w=0.04 m (40mm) |
| Steering disk | cylinder | r=0.065 m, h=0.025 m |
| Steering column | cylinder | r=0.028 m, h=0.11 m |
| Fork arms | box (×2) | 0.025 × 0.015 × 0.13 m |
| Shock absorber | cylinder | r=0.012 m, h=0.09 m |
| LiDAR | cylinder | r=0.035 m, h=0.06 m |
| Camera | box | 0.06 × 0.035 × 0.035 m |

### Key Positions

| Feature | X | Y | Z |
|---|---|---|---|
| Front axle | 0.2316 | — | — |
| Rear axle | -0.2284 | — | — |
| Left wheels | — | 0.238 | — |
| Right wheels | — | -0.238 | — |
| Steering joint | — | — | -0.055 |
| Wheel center | — | — | -0.179 |
| LiDAR | 0.36101 | -0.000993 | 0.35253 |
| Camera | 0.4056 | 0 | 0.21 |

## Debugging

```bash
# TF tree
ros2 run tf2_tools view_frames

# Controller list
ros2 control list_controllers

# Controller details
ros2 control list_controllers -v
ros2 control list_hardware_interfaces

# Joint states
ros2 topic echo /joint_states --once

# Topics
ros2 topic list | grep -E 'cmd|controller|joint'
```
