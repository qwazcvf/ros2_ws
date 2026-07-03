# nano_base_bridge

Jetson Nano ROS2 base bridge — safe `/cmd_vel` → `/odom` closed loop.

## Phase 1 Scope

**This package implements the interface loop ONLY.** The following are explicitly **excluded** from Phase 1:

- ❌ No Nav2 integration
- ❌ No LiDAR onboard processing
- ❌ No autonomous driving
- ❌ No SLAM / mapping
- ❌ No localization
- ❌ No path planning
- ❌ No real-vehicle ground contact testing

**Safety requirements for real chassis testing:**

- ⚠️ Real chassis testing MUST have wheels off the ground (jacked up)
- ⚠️ Real chassis testing MUST have emergency stop or power cutoff protection
- ⚠️ `hardware_mode` is a safety stub in Phase 1 — no real protocol is implemented
- ⚠️ `simulation_mode` is enabled by default

---

## Architecture

```
/cmd_vel (Twist)
    │
    ▼
ackermann_mapper  ─── raw BaseCommand
    │
    ▼
safety_manager    ─── safe BaseCommand
    │
    ├──▶ transport.send_command(safe_command)
    │       │
    │       ▼
    │   simulation_transport  (Phase 1 default)
    │   serial_transport      (stub, requires pyserial)
    │   can_transport         (stub, requires python-can)
    │
    ▼
odom_integrator   ─── simulation: uses safe_command
                  ─── hardware:   uses real feedback (only when connected+alive)
    │
    ├──▶ /odom (nav_msgs/Odometry)
    ├──▶ TF odom → base_link
    └──▶ /base/status (diagnostic_msgs/DiagnosticArray)
```

---

## Build

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select nano_base_bridge
source install/setup.bash
```

---

## Run (Simulation Mode — default)

```bash
ros2 launch nano_base_bridge base_bridge.launch.py
```

Or explicitly:

```bash
ros2 launch nano_base_bridge base_bridge.launch.py simulation_mode:=true
```

---

## Run (Hardware Mode — safety stub only)

```bash
ros2 launch nano_base_bridge base_bridge.launch.py simulation_mode:=false
```

**Without real hardware protocol the node will remain in STOP.**

---

## Inspection Commands

### Check node

```bash
ros2 node list
ros2 node info /nano_base_bridge_node
```

### Watch `/base/status`

```bash
ros2 topic echo /base/status
```

### Watch `/odom`

```bash
ros2 topic echo /odom
```

### Watch TF

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

---

## Test Commands

### Forward

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

### Backward

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: -0.04, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

### Left turn

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.30}}"
```

### Right turn

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.30}}"
```

### Stop

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

---

## Unit Tests

```bash
cd ~/ros2_ws
colcon test --packages-select nano_base_bridge
colcon test-result --verbose
```

---

## Default Parameters (Safety Highlights)

| Parameter | Default | Notes |
|---|---|---|
| `max_speed_mps` | 0.10 | Conservative forward limit |
| `max_reverse_speed_mps` | 0.05 | Conservative reverse limit |
| `allow_stationary_steering` | false | Pure angular.z → STOP |
| `simulation_mode` | true | Simulation by default |
| `cmd_vel_timeout_sec` | 0.5 | Timeout before auto-stop |
