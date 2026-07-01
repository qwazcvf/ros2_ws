# Inspection Bot Description — 4-Wheel Independent Steering

ROS 2 Humble robot description package for a **4-wheel independently-steered** inspection robot.

## Architecture

```
                    ┌─────────────────────────────┐
                    │        base_link             │  ← chassis (box 0.806×0.607×0.323 m)
                    │   ┌─────────────────────┐   │
                    │   │     hokuyo_link      │   │  ← LiDAR (fixed on top)
                    └──┼───┬─────────┬───┬────┼───┘
                       │   │         │   │    │
          ┌────────────┘   │         │   │    └────────────┐
          │                │         │   │                 │
      ┌───▼───────────┐  ┌─▼─────────▼─┐  ┌───────────▼───┐
      │ FL_steering   │  │ FR_steering  │  │ RL_steering    │  ...
      │   _link       │  │   _link      │  │   _link        │
      │ (continuous Z)│  │ (continuous Z)│  │ (continuous Z) │
      └───┬───────────┘  └──┬───────────┘  └───┬───────────┘
          │                 │                  │
      ┌───▼───────────┐  ┌──▼───────────┐  ┌───▼───────────┐
      │ FL_wheel      │  │ FR_wheel     │  │ RL_wheel       │
      │   _link       │  │   _link      │  │   _link        │
      │ (continuous Y)│  │ (continuous Y)│  │ (continuous Y) │
      └───────────────┘  └──────────────┘  └────────────────┘
```

## TF Tree

```
odom → base_link
        ├── front_left_steering_link  (steering joint: continuous, axis Z)
        │    └── front_left_wheel_link   (wheel joint: continuous, axis Y)
        ├── front_right_steering_link (steering joint: continuous, axis Z)
        │    └── front_right_wheel_link  (wheel joint: continuous, axis Y)
        ├── rear_left_steering_link   (steering joint: continuous, axis Z)
        │    └── rear_left_wheel_link    (wheel joint: continuous, axis Y)
        ├── rear_right_steering_link  (steering joint: continuous, axis Z)
        │    └── rear_right_wheel_link   (wheel joint: continuous, axis Y)
        └── hokuyo_link  (fixed joint)
```

## Joints

| Joint | Type | Parent | Child | Axis | Control |
|---|---|---|---|---|---|
| `front_left_steering_joint` | continuous | base_link | fl_steering_link | Z | position |
| `front_right_steering_joint` | continuous | base_link | fr_steering_link | Z | position |
| `rear_left_steering_joint` | continuous | base_link | rl_steering_link | Z | position |
| `rear_right_steering_joint` | continuous | base_link | rr_steering_link | Z | position |
| `front_left_wheel_joint` | continuous | fl_steering_link | fl_wheel_link | Y | velocity |
| `front_right_wheel_joint` | continuous | fr_steering_link | fr_wheel_link | Y | velocity |
| `rear_left_wheel_joint` | continuous | rl_steering_link | rl_wheel_link | Y | velocity |
| `rear_right_wheel_joint` | continuous | rr_steering_link | rr_wheel_link | Y | velocity |
| `hokuyo_joint` | fixed | base_link | hokuyo_link | — | — |

## How This Differs from the Original Ackermann Model

| Aspect | Original (Before) | Refactored (Now) |
|---|---|---|
| **Steering joints** | Front-only (±0.6 rad revolute) | All 4 corners (continuous, 360°) |
| **Rear wheels** | Directly connected to base_link | Each has its own steering joint |
| **Joint type** | revolute with hard limits | continuous (unbounded) |
| **Gazebo plugin** | `libgazebo_ros_ackermann_drive.so` | `libgz_ros2_control-system.so` + ros2_control |
| **URDF format** | Raw URDF with duplicated geometry | xacro with `corner` macro |
| **Controller** | AckermannSteering (bicycle model) | Direct joint control: position (steer) + velocity (drive) |
| **Joint names** | `left_steering_joint`, `left_front_wheel_joint`, etc. | Uniform: `{fl,fr,rl,rr}_{steering,wheel}_joint` |

## Why Not Ackermann?

Ackermann steering geometry is designed for **front-steering cars** where the inner front wheel turns more sharply than the outer front wheel due to the steering linkage geometry. This model assumes:
- Only front wheels steer
- Rear wheels are fixed
- Steering angles follow the Ackermann formula

Your real robot has **4 independent 360° steering servos** — each corner can point in any direction independently. This enables:
- Crab steering (sideways motion)
- Zero-radius turns (spot rotation)
- Diagonal driving

**These motions are impossible with an Ackermann controller.**

## 360° Steering with ros2_control

- **Joint type**: `continuous` (no angle limits)
- **Command interface**: `position` — `position_controllers/JointGroupPositionController`
- **Why it works**: The position controller sends absolute angle commands. Since the joint is continuous, there are no hard limits. The Gazebo physics engine handles multi-turn wrapping.
- **On real hardware**: If using actual 360° servos, you'd implement a custom `hardware_interface` that maps position commands to servo PWM/duty cycle.

> **Alternative**: If `JointGroupPositionController` doesn't handle continuous joints well (e.g., wrapping issues), switch to `joint_trajectory_controller/JointTrajectoryController` which supports continuous joints natively.

## Package Structure

```
inspection_bot_description/
├── config/
│   └── controllers.yaml          # ros2_control configuration
├── inspection_bot_description/
│   ├── __init__.py
│   └── keyboard_control.py       # 4-wheel keyboard controller
├── launch/
│   ├── display.launch.py         # RViz only (no simulator needed)
│   ├── gazebo.launch.py          # Classic Gazebo 11
│   └── gz_sim.launch.py          # Ignition Gazebo (Fortress)
├── meshes/                       # STL meshes (from original; unused with box/cylinder)
├── rviz/
│   └── display.rviz              # RViz configuration
├── urdf/
│   ├── robot.xacro               # Main xacro file with corner macro
│   ├── robot.urdf                # Original URDF (kept for reference)
│   └── robot.csv                 # Original CSV (kept for reference)
├── worlds/
│   └── empty.world               # Empty Gazebo world
├── package.xml
├── setup.py
└── setup.cfg
```

## Installation

### 1. Prerequisites (Jetson / ARM64)

```bash
# Base ROS 2 Humble should already be installed at /opt/ros/humble

# For RViz display only (no simulation):
sudo apt install ros-humble-joint-state-publisher-gui

# For Ignition Gazebo simulation:
sudo apt install ros-humble-ros-gz-sim ros-humble-gz-ros2-control

# For controller management:
sudo apt install ros-humble-controller-manager \
                 ros-humble-joint-state-broadcaster \
                 ros-humble-position-controllers \
                 ros-humble-velocity-controllers
```

### 2. Build

```bash
cd ~/ros2_ws
colcon build --packages-select inspection_bot_description --symlink-install
source install/setup.bash
```

## Usage

### RViz Display (no simulator, works immediately)

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch inspection_bot_description display.launch.py
```

Then use the `joint_state_publisher_gui` sliders to manually move each joint.

### Ignition Gazebo Simulation

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch inspection_bot_description gz_sim.launch.py
```

### Classic Gazebo 11 Simulation

```bash
# First edit robot.xacro: switch the plugin to libgazebo_ros2_control.so
source ~/ros2_ws/install/setup.bash
ros2 launch inspection_bot_description gazebo.launch.py
```

### Keyboard Control

In a new terminal:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run inspection_bot_description keyboard_control
```

Controls:
| Key | Action |
|---|---|
| W / S | Accelerate / Decelerate (all 4 wheels) |
| A / D | Steer Left / Right (normal turn — all wheels) |
| Q / E | Crab steer Left / Right |
| Z / C | Spot rotate CCW / CW |
| Space | Emergency stop + center steering |
| Esc / q | Quit |

### Manual Joint Commands (for testing individual joints)

```bash
# Set all steering angles to 30° (0.524 rad)
ros2 topic pub /steering_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [0.524, 0.524, 0.524, 0.524]}" -1

# Set all wheel velocities to 5 rad/s
ros2 topic pub /drive_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [5.0, 5.0, 5.0, 5.0]}" -1
```

## Debugging Commands

```bash
# Check TF tree
ros2 run tf2_tools view_frames

# Check joint states
ros2 topic echo /joint_states

# List active controllers
ros2 control list_controllers

# Check controller state
ros2 control list_hardware_interfaces

# Monitor TF in RViz
ros2 launch inspection_bot_description display.launch.py
# In RViz: Add → TF → check the tree
```

## Controller Architecture

```
┌─────────────────────────────────────────┐
│         controller_manager              │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  joint_state_broadcaster       │    │
│  │  → /joint_states (all 8 joints)│    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  steering_controller            │    │
│  │  JointGroupPositionController   │    │
│  │  ← /steering_controller/commands│    │
│  │  → [fl, fr, rl, rr] (rad)      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  drive_controller               │    │
│  │  JointGroupVelocityController   │    │
│  │  ← /drive_controller/commands   │    │
│  │  → [fl, fr, rl, rr] (rad/s)    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Hardware: GazeboSimSystem              │
│  (gz_ros2_control/GazeboSystem)         │
└─────────────────────────────────────────┘
```

## Geometry

| Part | Shape | Dimensions |
|---|---|---|
| Chassis (`base_link`) | box | 0.806 × 0.607 × 0.323 m |
| Steering knuckle | cylinder | r=0.03 m, h=0.06 m |
| Wheel | cylinder | r=0.076 m (76mm), w=0.04 m (40mm) |
| LiDAR | cylinder | r=0.03 m, h=0.05 m |
| Wheel position (x, y) | — | (±0.25, ±0.24) m |
| Wheel Z offset | — | -0.09 m (relative to chassis center) |

## Future: Real Hardware Integration

For real hardware, you'll need:
1. A custom `hardware_interface` plugin implementing `ros2_control::SystemInterface`
2. Map `read()`/`write()` to your motor drivers (CAN, serial, etc.)
3. Replace `GazeboSimSystem` with your hardware plugin in the `<ros2_control>` URDF tag
4. The controllers (`steering_controller`, `drive_controller`) remain the same — ros2_control abstracts the hardware

## Custom 4-Wheel Kinematics Controller

The current setup uses simple joint-level controllers. For a full autonomous stack, you'd want a **kinematics-level controller** that:

- Takes `geometry_msgs/Twist` (cmd_vel) as input
- Computes individual steering angles and wheel velocities for each corner
- Supports multiple modes: normal, crab, spot-turn
- Publishes to `/steering_controller/commands` and `/drive_controller/commands`

This is a natural evolution of `keyboard_control.py` and can be implemented as a separate ROS 2 node.
