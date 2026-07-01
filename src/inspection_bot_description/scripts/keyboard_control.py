#!/usr/bin/env python3
"""
4-Wheel Independent Steering Keyboard Controller.

Controls:
  W / S     : accelerate / decelerate (all 4 wheels)
  A / D     : steer left / right (all 4 wheels turn together, normal turn)
  Q / E     : crab steer (all wheels same direction for sideways motion)
  Z / C     : zero-turn (front & rear steer opposite for spot rotation)
  SPACE     : emergency stop + center steering
  ESC / q   : quit

Publishes:
  /steering_controller/commands   (Float64MultiArray, 4 values, rad)
  /drive_controller/commands      (Float64MultiArray, 4 values, rad/s)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import sys
import termios
import tty
import select

# ====================== Configuration ======================
MAX_SPEED  = 20.0    # max wheel velocity (rad/s)
MAX_STEER  = 3.1416  # max steering angle (rad, ±π for 360°)
STEP_SPEED = 2.0     # speed increment per keypress
STEP_STEER = 0.15    # steering increment per keypress
PUB_RATE   = 0.05    # publish interval (seconds)
# ===========================================================

HELP_MSG = """
╔══════════════════════════════════════════════════════════════╗
║     Inspection Bot — 4-Wheel Independent Steering           ║
╠══════════════════════════════════════════════════════════════╣
║  W / S    : Accelerate / Decelerate (all wheels)            ║
║  A / D    : Steer Left / Right (normal turn)                ║
║  Q / E    : Crab Left / Right (sideways)                    ║
║  Z / C    : Spot-rotate CCW / CW                            ║
║  SPACE    : Emergency stop + center steering                ║
║  ESC / q  : Quit                                            ║
╚══════════════════════════════════════════════════════════════╝
"""

settings = None


def get_key():
    """Non-blocking single-key read."""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = rlist[0].read(1) if rlist else ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class FourWheelKeyboardController(Node):
    def __init__(self):
        super().__init__("keyboard_controller")

        self.pub_steering = self.create_publisher(
            Float64MultiArray, "/steering_controller/commands", 10
        )
        self.pub_drive = self.create_publisher(
            Float64MultiArray, "/drive_controller/commands", 10
        )

        self.speed = 0.0          # wheel velocity (rad/s)
        self.steer_normal = 0.0   # steering angle for normal/crab mode (rad)
        self.steer_rotate = 0.0   # steering angle for spot-rotate mode (rad)

        # Publish continuously so robot keeps moving after key release
        self.timer = self.create_timer(PUB_RATE, self.publish_commands)

    def publish_commands(self):
        """Compute and publish steering + drive commands."""

        # ── Steering command [fl, fr, rl, rr] ──
        # Normal turn: front & rear steer SAME direction → arcs
        # Spot rotate: fl & rr steer one way, fr & rl steer opposite
        fl_steer = self.steer_normal + self.steer_rotate
        fr_steer = self.steer_normal - self.steer_rotate
        rl_steer = self.steer_normal - self.steer_rotate
        rr_steer = self.steer_normal + self.steer_rotate

        steer_msg = Float64MultiArray()
        steer_msg.data = [fl_steer, fr_steer, rl_steer, rr_steer]
        self.pub_steering.publish(steer_msg)

        # ── Drive command [fl, fr, rl, rr] ──
        drive_msg = Float64MultiArray()
        drive_msg.data = [self.speed] * 4
        self.pub_drive.publish(drive_msg)

        # ── Status line ──
        print(
            f"\r  speed: {self.speed:+6.2f} rad/s |"
            f"  steer: {self.steer_normal:+6.2f} / {self.steer_rotate:+6.2f} rad  ",
            end="",
            flush=True,
        )


def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = FourWheelKeyboardController()

    print(HELP_MSG)

    try:
        while rclpy.ok():
            key = get_key()

            if key == "w":
                node.speed = min(MAX_SPEED, node.speed + STEP_SPEED)
            elif key == "s":
                node.speed = max(-MAX_SPEED, node.speed - STEP_SPEED)

            # Normal steering (A/D)
            elif key == "a":
                node.steer_normal = min(MAX_STEER, node.steer_normal + STEP_STEER)
            elif key == "d":
                node.steer_normal = max(-MAX_STEER, node.steer_normal - STEP_STEER)

            # Crab steering (Q/E) — same mechanism, different label
            elif key == "q":
                node.steer_normal = min(MAX_STEER, node.steer_normal + STEP_STEER)
            elif key == "e":
                node.steer_normal = max(-MAX_STEER, node.steer_normal - STEP_STEER)

            # Spot rotate (Z/C)
            elif key == "z":
                node.steer_rotate = min(MAX_STEER, node.steer_rotate + STEP_STEER)
            elif key == "c":
                node.steer_rotate = max(-MAX_STEER, node.steer_rotate - STEP_STEER)

            # Emergency stop
            elif key == " ":
                node.speed = 0.0
                node.steer_normal = 0.0
                node.steer_rotate = 0.0
                print("\n*** EMERGENCY STOP ***")

            # Quit
            elif key in ("\x1b", "q", "\x03"):
                break

            # Spin once to let the timer callback fire
            rclpy.spin_once(node, timeout_sec=0.01)

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Send zero commands before shutting down
        stop = Float64MultiArray()
        stop.data = [0.0, 0.0, 0.0, 0.0]
        node.pub_steering.publish(stop)
        node.pub_drive.publish(stop)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print("\nController stopped.")


if __name__ == "__main__":
    main()
