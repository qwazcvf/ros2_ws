"""
base_bridge_node.py — Main ROS2 node for the nano base bridge.

Closed loop:
  /cmd_vel → ackermann_mapper → safety_manager → safe_command
  → transport.send_command(safe_command)
  → odom_integrator (using safe_command in sim mode, feedback in hw mode)
  → /odom + TF (odom → base_link)
  → /base/status
"""

import time
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from diagnostic_msgs.msg import DiagnosticArray
from tf2_ros import TransformBroadcaster

from .protocol import BaseCommand, BaseFeedback
from .ackermann_mapper import AckermannMapper
from .safety_manager import SafetyManager
from .odom_integrator import OdomIntegrator
from .base_status import BaseStatusPublisher
from .transport.simulation_transport import SimulationTransport
from .transport.serial_transport import SerialTransport
from .transport.can_transport import CanTransport


class NanoBaseBridgeNode(Node):
    """ROS2 Node that implements the full cmd_vel → odom safe closed loop."""

    def __init__(self):
        super().__init__("nano_base_bridge_node")

        # --- Declare and read all parameters ---
        self._declare_parameters()
        self._read_parameters()

        # --- Subscribers ---
        self._cmd_vel_sub = self.create_subscription(
            Twist,
            self._cmd_vel_topic,
            self._cmd_vel_callback,
            10,
        )

        # --- Publishers ---
        self._odom_pub = self.create_publisher(Odometry, self._odom_topic, 10)
        self._status_pub = self.create_publisher(DiagnosticArray, self._status_topic, 10)

        # --- TF broadcaster ---
        self._tf_broadcaster = TransformBroadcaster(self)

        # --- Pipeline components ---
        self._ackermann_mapper = AckermannMapper(self._params_flat)
        self._safety_manager = SafetyManager(self._params_flat)
        self._odom_integrator = OdomIntegrator(self._params_flat)
        self._status_builder = BaseStatusPublisher()

        # --- Transport ---
        self._transport = self._create_transport()

        # --- State ---
        self._last_cmd_vel_msg = Twist()
        self._last_cmd_vel_time = 0.0
        self._first_cmd_vel_received = False

        # --- Timers ---
        self._control_timer = self.create_timer(
            1.0 / self._control_rate_hz, self._control_loop
        )
        self._status_timer = self.create_timer(
            1.0 / self._status_rate_hz, self._publish_status
        )

        # --- Transport connect ---
        if not self._transport.connect():
            if not self._simulation_mode:
                self.get_logger().warn(
                    "Hardware mode: transport connection failed — node will stay in STOP."
                )
            else:
                self.get_logger().info(
                    "Simulation mode: using simulated transport."
                )

        self.get_logger().info(
            f"NanoBaseBridgeNode started — "
            f"simulation_mode={self._simulation_mode}, "
            f"control_rate={self._control_rate_hz} Hz"
        )

    # ------------------------------------------------------------------
    #  Parameter handling
    # ------------------------------------------------------------------

    def _declare_parameters(self):
        """Declare all parameters with safe defaults."""
        # Mode
        self.declare_parameter("simulation_mode", True)
        self.declare_parameter("hardware_transport", "serial")

        # Topics
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("status_topic", "/base/status")

        # Frames
        self.declare_parameter("odom_frame_id", "odom")
        self.declare_parameter("base_frame_id", "base_link")
        self.declare_parameter("publish_tf", True)

        # Rates
        self.declare_parameter("control_rate_hz", 50.0)
        self.declare_parameter("status_rate_hz", 5.0)

        # Vehicle geometry
        self.declare_parameter("wheel_base_m", 0.55)
        self.declare_parameter("track_width_m", 0.45)
        self.declare_parameter("wheel_radius_m", 0.08)

        # Speed limits
        self.declare_parameter("max_speed_mps", 0.10)
        self.declare_parameter("max_reverse_speed_mps", 0.05)
        self.declare_parameter("max_angular_speed_radps", 0.50)
        self.declare_parameter("max_steering_angle_rad", 0.35)

        # Deadbands
        self.declare_parameter("linear_deadband_mps", 0.02)
        self.declare_parameter("angular_deadband_radps", 0.03)

        # Ackermann
        self.declare_parameter("min_speed_for_ackermann_mps", 0.05)
        self.declare_parameter("allow_stationary_steering", False)
        self.declare_parameter("allow_pure_angular_crawl", False)
        self.declare_parameter("pure_angular_crawl_speed_mps", 0.00)

        # Safety
        self.declare_parameter("cmd_vel_timeout_sec", 0.5)
        self.declare_parameter("hardware_feedback_timeout_sec", 0.5)
        self.declare_parameter("communication_timeout_sec", 0.5)
        self.declare_parameter("send_stop_on_startup", True)
        self.declare_parameter("send_stop_on_shutdown", True)
        self.declare_parameter("stop_on_estop", True)

        # Battery
        self.declare_parameter("battery_warn_voltage", 21.0)
        self.declare_parameter("battery_stop_voltage", 19.0)
        self.declare_parameter("enable_low_voltage_stop", False)

        # Serial
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("serial_baudrate", 115200)
        self.declare_parameter("serial_timeout_sec", 0.05)

        # CAN
        self.declare_parameter("can_interface", "can0")
        self.declare_parameter("can_bitrate", 500000)

        # Direction inversion
        self.declare_parameter("invert_speed", False)
        self.declare_parameter("invert_steering", False)

        # Covariance
        self.declare_parameter(
            "odom_pose_covariance_diagonal",
            [0.05, 0.05, 9999.0, 9999.0, 9999.0, 0.20],
        )
        self.declare_parameter(
            "odom_twist_covariance_diagonal",
            [0.05, 0.05, 9999.0, 9999.0, 9999.0, 0.20],
        )

    def _read_parameters(self):
        """Read all parameters into a flat dict for component constructors."""
        keys = [
            "simulation_mode", "hardware_transport",
            "cmd_vel_topic", "odom_topic", "status_topic",
            "odom_frame_id", "base_frame_id", "publish_tf",
            "control_rate_hz", "status_rate_hz",
            "wheel_base_m", "track_width_m", "wheel_radius_m",
            "max_speed_mps", "max_reverse_speed_mps",
            "max_angular_speed_radps", "max_steering_angle_rad",
            "linear_deadband_mps", "angular_deadband_radps",
            "min_speed_for_ackermann_mps",
            "allow_stationary_steering", "allow_pure_angular_crawl",
            "pure_angular_crawl_speed_mps",
            "cmd_vel_timeout_sec", "hardware_feedback_timeout_sec",
            "communication_timeout_sec",
            "send_stop_on_startup", "send_stop_on_shutdown", "stop_on_estop",
            "battery_warn_voltage", "battery_stop_voltage", "enable_low_voltage_stop",
            "serial_port", "serial_baudrate", "serial_timeout_sec",
            "can_interface", "can_bitrate",
            "invert_speed", "invert_steering",
            "odom_pose_covariance_diagonal", "odom_twist_covariance_diagonal",
        ]
        self._params_flat = {}
        for key in keys:
            self._params_flat[key] = self.get_parameter(key).value

        # Convenience attributes
        self._simulation_mode = bool(self._params_flat["simulation_mode"])
        self._cmd_vel_topic = str(self._params_flat["cmd_vel_topic"])
        self._odom_topic = str(self._params_flat["odom_topic"])
        self._status_topic = str(self._params_flat["status_topic"])
        self._publish_tf = bool(self._params_flat["publish_tf"])
        self._control_rate_hz = float(self._params_flat["control_rate_hz"])
        self._status_rate_hz = float(self._params_flat["status_rate_hz"])

    # ------------------------------------------------------------------
    #  Transport factory
    # ------------------------------------------------------------------

    def _create_transport(self):
        """Create the appropriate transport based on parameters."""
        transport_type = str(self._params_flat.get("hardware_transport", "serial")).lower()

        if self._simulation_mode:
            return SimulationTransport()

        if transport_type == "serial":
            return SerialTransport(
                port=str(self._params_flat.get("serial_port", "/dev/ttyUSB0")),
                baudrate=int(self._params_flat.get("serial_baudrate", 115200)),
                timeout=float(self._params_flat.get("serial_timeout_sec", 0.05)),
            )
        elif transport_type == "can":
            return CanTransport(
                interface=str(self._params_flat.get("can_interface", "can0")),
                bitrate=int(self._params_flat.get("can_bitrate", 500000)),
            )
        else:
            self.get_logger().warn(
                f"Unknown transport type '{transport_type}', falling back to SimulationTransport."
            )
            return SimulationTransport()

    # ------------------------------------------------------------------
    #  Callbacks
    # ------------------------------------------------------------------

    def _cmd_vel_callback(self, msg: Twist):
        """Store the latest /cmd_vel message and its arrival time."""
        self._last_cmd_vel_msg = msg
        self._last_cmd_vel_time = self.get_clock().now().nanoseconds * 1e-9
        if not self._first_cmd_vel_received:
            self._first_cmd_vel_received = True
            self.get_logger().info("First /cmd_vel received.")

    # ------------------------------------------------------------------
    #  Control loop
    # ------------------------------------------------------------------

    def _control_loop(self):
        """
        Main control loop (runs at control_rate_hz).

        Order:
          1. Get current time
          2. ackermann_mapper → raw_command
          3. Read feedback (simulated or real)
          4. safety_manager → safe_command
          5. transport.send_command(safe_command)
          6. Integrate odom (safe_command in sim, feedback in hw)
          7. Publish /odom
          8. Publish TF odom → base_link
        """
        now = self.get_clock().now()
        now_sec = now.nanoseconds * 1e-9

        # --- Step 2: Map cmd_vel to ackermann command ---
        if self._first_cmd_vel_received:
            linear_x = self._last_cmd_vel_msg.linear.x
            angular_z = self._last_cmd_vel_msg.angular.z
        else:
            linear_x = 0.0
            angular_z = 0.0

        raw_command = self._ackermann_mapper.map(linear_x, angular_z, now_sec)

        # --- Step 3: Read feedback ---
        feedback = self._transport.read_feedback()

        # --- Step 4: Safety evaluation ---
        transport_connected = self._transport.is_connected()
        safe_command, safety_state = self._safety_manager.evaluate(
            raw_command,
            self._last_cmd_vel_time,
            now_sec,
            feedback,
            transport_connected,
        )

        # --- Step 5: Send command to transport ---
        self._transport.send_command(safe_command)

        # --- Step 6: Integrate odometry ---
        if self._simulation_mode:
            # Simulation: use safe_command
            self._odom_integrator.update_from_safe_command(
                safe_command.speed_mps,
                safe_command.steering_angle_rad,
                now_sec,
            )
        else:
            # Hardware mode: use real feedback ONLY if connected and alive
            if safety_state.hardware_connected and safety_state.feedback_alive:
                self._odom_integrator.update_from_feedback(
                    feedback.speed_mps,
                    feedback.steering_angle_rad,
                    now_sec,
                )
            # else: no real feedback → do NOT integrate (stay put)

        # ---- Step 7: Publish /odom ---
        v = safe_command.speed_mps
        omega = 0.0
        if abs(v) > 1e-9:
            omega = v / self._params_flat.get("wheel_base_m", 0.55) * math.tan(
                safe_command.steering_angle_rad
            )

        odom_msg = self._odom_integrator.build_odometry_msg(now.to_msg(), v, omega)
        self._odom_pub.publish(odom_msg)

        # --- Step 8: Publish TF ---
        if self._publish_tf:
            tf_msg = self._odom_integrator.build_tf_msg(now.to_msg())
            self._tf_broadcaster.sendTransform(tf_msg)

        # --- Store safety state for status publisher ---
        self._last_safety_state = safety_state
        self._last_safe_command = safe_command
        self._last_feedback = feedback

    # ------------------------------------------------------------------
    #  Status publisher
    # ------------------------------------------------------------------

    def _publish_status(self):
        """Periodic status publication."""
        now = self.get_clock().now()

        safety = getattr(self, "_last_safety_state", None)
        cmd = getattr(self, "_last_safe_command", None)
        fb = getattr(self, "_last_feedback", None)

        if safety is None or cmd is None or fb is None:
            # Not yet run a control loop — publish initial STOP status
            arr = self._status_builder.build(
                stamp=now.to_msg(),
                simulation_mode=self._simulation_mode,
                motion_mode="STOP",
                speed_mps=0.0,
                steering_angle_rad=0.0,
                cmd_vel_alive=False,
                cmd_vel_timeout=False,
                hardware_connected=self._transport.is_connected(),
                feedback_alive=self._simulation_mode,
                feedback_timeout=False,
                estop_active=False,
                battery_voltage=24.0,
                battery_percentage=100.0,
                error_code=0,
                error_text="",
                last_stop_reason="startup",
                odom_x=0.0,
                odom_y=0.0,
                odom_yaw=0.0,
                control_rate_hz=self._control_rate_hz,
            )
            self._status_pub.publish(arr)
            return

        arr = self._status_builder.build(
            stamp=now.to_msg(),
            simulation_mode=self._simulation_mode,
            motion_mode=cmd.motion_mode,
            speed_mps=cmd.speed_mps,
            steering_angle_rad=cmd.steering_angle_rad,
            cmd_vel_alive=safety.cmd_vel_alive,
            cmd_vel_timeout=safety.cmd_vel_timeout,
            hardware_connected=safety.hardware_connected,
            feedback_alive=safety.feedback_alive,
            feedback_timeout=safety.feedback_timeout,
            estop_active=safety.estop_active,
            battery_voltage=fb.battery_voltage,
            battery_percentage=fb.battery_percentage,
            error_code=fb.error_code,
            error_text=fb.error_text,
            last_stop_reason=safety.last_stop_reason,
            odom_x=self._odom_integrator.x,
            odom_y=self._odom_integrator.y,
            odom_yaw=self._odom_integrator.yaw,
            control_rate_hz=self._control_rate_hz,
        )
        self._status_pub.publish(arr)

    # ------------------------------------------------------------------
    #  Shutdown
    # ------------------------------------------------------------------

    def shutdown(self):
        """Send STOP command and clean up."""
        self.get_logger().info("Shutting down — sending final STOP.")
        stop_cmd = self._safety_manager.shutdown()
        self._transport.send_command(stop_cmd)
        self._transport.disconnect()

    def destroy_node(self):
        self.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = NanoBaseBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
