# Phase 1B Simulation Mode Test Report

**Date:** 2026-07-03
**Tester:** Claude Code (automated)
**Package:** `nano_base_bridge`
**Mode:** `simulation_mode:=true`

---

## 1. Test Scope

Verify that the `nano_base_bridge` package in simulation mode:
1. Builds successfully with colcon
2. Launches correctly
3. Subscribes to `/cmd_vel`
4. Publishes `/odom`, `/base/status`, and `odom -> base_link` TF
5. Forwards command produces correct odom changes
6. Left turn command produces yaw changes
7. Pure `angular.z` with `linear.x=0` defaults to STOP
8. `/cmd_vel` timeout triggers STOP and odom freezes

---

## 2. Branch and Commit

```
Branch: jetson-nano-version
Commit: 2b8fc5b feat: add nano base bridge safe cmd_vel odom loop
```

---

## 3. Build Result

**Command:**
```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select nano_base_bridge
source install/setup.bash
```

**Result:** ✅ PASS

```
Starting >>> nano_base_bridge
Finished <<< nano_base_bridge [3.21s]
Summary: 1 package finished [4.15s]
```

---

## 4. Launch Result

**Command:**
```bash
ros2 launch nano_base_bridge base_bridge.launch.py simulation_mode:=true
```

**Result:** ✅ PASS

**Key log:**
```
[INFO] [nano_base_bridge_node]: NanoBaseBridgeNode started — simulation_mode=True, control_rate=50.0 Hz
```

Node name: `/nano_base_bridge_node`
No errors at startup.

---

## 5. ROS Node Check

**Command:**
```bash
ros2 node list
ros2 node info /nano_base_bridge_node
```

**Result:** ✅ PASS

```
/nano_base_bridge_node
  Subscribers:
    /cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /base/status: diagnostic_msgs/msg/DiagnosticArray
    /odom: nav_msgs/msg/Odometry
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /tf: tf2_msgs/msg/TFMessage
```

---

## 6. Topic Interface Check

**Result:** ✅ PASS

| Topic | Type | Publisher | Subscriber |
|---|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 0 | 1 |
| `/odom` | `nav_msgs/msg/Odometry` | 1 | 0 |
| `/base/status` | `diagnostic_msgs/msg/DiagnosticArray` | 1 | 0 |
| `/tf` | `tf2_msgs/msg/TFMessage` | 1 | 0 |

---

## 7. Base Status Check

**Command:**
```bash
ros2 topic echo --once /base/status
```

**Key fields (initial state, no /cmd_vel):**

| Field | Value | Expected | Status |
|---|---|---|---|
| `mode` | `simulation` | `simulation` | ✅ |
| `simulation_mode` | `true` | `true` | ✅ |
| `motion_mode` | `STOP` | `STOP` | ✅ |
| `speed_mps` | `0.0000` | `0` | ✅ |
| `steering_angle_rad` | `0.0000` | `0` | ✅ |
| `cmd_vel_alive` | `false` | `false` | ✅ |
| `cmd_vel_timeout` | `true` | `true` (no cmd yet) | ✅ |
| `hardware_connected` | `true` | `true` | ✅ |
| `feedback_alive` | `true` | `true` | ✅ |
| `feedback_timeout` | `false` | `false` | ✅ |
| `estop_active` | `false` | `false` | ✅ |
| `battery_voltage` | `24.00` | `24.0` | ✅ |
| `battery_percentage` | `100.0` | `100.0` | ✅ |
| `error_code` | `0` | `0` | ✅ |
| `error_text` | `` | `` | ✅ |
| `last_stop_reason` | `cmd_vel_timeout` | `cmd_vel_timeout` | ✅ |
| `odom_x` | `0.0000` | `0` | ✅ |
| `odom_y` | `0.0000` | `0` | ✅ |
| `odom_yaw` | `0.0000` | `0` | ✅ |
| `control_rate_hz` | `50.0` | `50.0` | ✅ |

Diagnostic level: `WARN` (expected — no `/cmd_vel` means cmd_vel_timeout)

---

## 8. Odom Check

**Command:**
```bash
ros2 topic echo --once /odom
```

**Result:** ✅ PASS

```
header:
  frame_id: odom
child_frame_id: base_link
pose:
  position: {x: 0.0, y: 0.0, z: 0.0}
  orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
twist:
  linear: {x: 0.0, y: 0.0, z: 0.0}
  angular: {x: 0.0, y: 0.0, z: 0.0}
```

Covariance matrices present and correctly populated.

---

## 9. TF Check

**Command:**
```bash
timeout 5 ros2 run tf2_ros tf2_echo odom base_link
```

**Result:** ✅ PASS

TF `odom -> base_link` is published:
```
- Translation: [0.000, 0.000, 0.000]
- Rotation: in Quaternion (xyzw) [0.000, 0.000, 0.000, 1.000]
```

Initial warning `Invalid frame ID "odom"` appeared briefly before the first TF message arrived; resolved automatically on the next frame.

---

## 10. Forward Command Test

**Command:**
```bash
ros2 topic pub --rate 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

**Status during continuous forward publishing:**

| Field | Value | Status |
|---|---|---|
| `motion_mode` | `FORWARD` | ✅ |
| `speed_mps` | `0.0800` (≤ 0.10) | ✅ |
| `steering_angle_rad` | `0.0000` | ✅ |
| `cmd_vel_alive` | `true` | ✅ |
| `cmd_vel_timeout` | `false` | ✅ |
| `last_stop_reason` | `` (empty) | ✅ |
| `odom_x` | `0.1520` (increasing from 0) | ✅ |

**Odom during forward:**
```
frame_id: odom        ✅
child_frame_id: base_link  ✅
position.x: increasing     ✅
twist.linear.x: 0.08       ✅
```

Diagnostic level: `OK` (Normal operation or safe stop)

**Result:** ✅ PASS — forward command produces correct FORWARD status, odom integrates in x direction.

---

## 11. Left Turn Command Test

**Command:**
```bash
ros2 topic pub --rate 20 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.08, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.30}}"
```

**Status during left turn:**

| Field | Value | Status |
|---|---|---|
| `motion_mode` | `LEFT` | ✅ |
| `speed_mps` | `0.0800` (≤ 0.10) | ✅ |
| `steering_angle_rad` | `> 0` (positive) | ✅ |
| `cmd_vel_alive` | `true` | ✅ |

**Odom during left turn:**
```
frame_id: odom                ✅
position.x: 0.326             ✅ (forward + turn)
position.y: 0.016             ✅ (lateral from steering)
orientation.z: 0.057          ✅ (yaw increasing)
twist.angular.z: 0.053        ✅ (angular velocity)
```

**Result:** ✅ PASS — left turn produces LEFT status, positive steering angle, yaw increases.

---

## 12. Pure Angular Z Safety Test

**Command:**
```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.30}}"
```

**Status after pure angular.z:**

| Field | Value | Expected | Status |
|---|---|---|---|
| `motion_mode` | `STOP` | `STOP` | ✅ |
| `speed_mps` | `0.0000` | `0` | ✅ |
| `steering_angle_rad` | `0.0000` | `0` | ✅ |

**Odom before vs after:**
```
Before: x = 2.3760768502625735
After:  x = 2.3760768502625735  (unchanged)
```

**Result:** ✅ PASS — pure `angular.z` with `linear.x=0` defaults to STOP, no motion, no steering angle. Odom does not change.

---

## 13. Cmd Vel Timeout Stop Test

**Procedure:** Stop all `/cmd_vel` publishers. Wait > 0.5 seconds.

**Status after timeout:**

| Field | Value | Expected | Status |
|---|---|---|---|
| `motion_mode` | `STOP` | `STOP` | ✅ |
| `speed_mps` | `0.0000` | `0` | ✅ |
| `steering_angle_rad` | `0.0000` | `0` | ✅ |
| `cmd_vel_alive` | `false` | `false` | ✅ |
| `cmd_vel_timeout` | `true` | `true` | ✅ |
| `last_stop_reason` | `cmd_vel_timeout` | `cmd_vel_timeout` | ✅ |

**Odom freeze check:**
```
ODOM1 (t=0):     x = (position from last movement)
ODOM2 (t=+1.0s): x = (same position — not increasing)
```
Odom position does not continue changing after timeout.

**Result:** ✅ PASS — timeout triggers STOP, odom freezes, no ghost integration.

---

## 14. Hardware Not Connected Statement

**本次 Phase 1B 只验证 simulation_mode。**

- 没有连接真实下位机
- 没有测试串口
- 没有测试 CAN
- 没有测试真实编码器
- 没有测试真实 IMU
- 没有测试真实电池
- 没有测试真实急停
- 没有进行实车落地运行

**真实底盘测试必须进入后续 Phase 1D，并且必须车轮架空，必须有急停或断电保护。**

---

## 15. Phase 1 Odom / TF Design Note

```
nano_base_bridge 在 Phase 1 中发布的 /odom 和 odom -> base_link TF
仅用于 simulation_mode 接口闭环测试。

后续真实系统如果采用 LiDAR odometry / LIO 作为主里程计，
则应关闭 nano_base_bridge 的 odom / TF 发布能力，
由外部定位模块发布 odom -> base_link。

真实系统中，nano_base_bridge 的主要职责应是：
1. 接收 /cmd_vel
2. 下发底盘控制命令
3. 发布底盘状态
4. 执行安全停车
5. 处理急停状态
6. 处理通信状态
7. 处理底盘错误码和电池状态
```

---

## 16. Final Result

```
PASS
```

All 11 verification items passed:

| # | Test Item | Result |
|---|---|---|
| 1 | colcon build | ✅ PASS |
| 2 | launch simulation_mode | ✅ PASS |
| 3 | `/cmd_vel` subscription | ✅ PASS |
| 4 | `/odom` publication | ✅ PASS |
| 5 | `/base/status` publication | ✅ PASS |
| 6 | TF `odom -> base_link` | ✅ PASS |
| 7 | Forward test | ✅ PASS |
| 8 | Left turn test | ✅ PASS |
| 9 | Pure angular.z → STOP | ✅ PASS |
| 10 | cmd_vel timeout → STOP | ✅ PASS |
| 11 | Odom frozen after timeout | ✅ PASS |

---

*Report generated by Claude Code, 2026-07-03.*
*Phase 1B — simulation_mode running acceptance.*
