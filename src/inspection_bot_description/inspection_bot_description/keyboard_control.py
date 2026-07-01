#!/usr/bin/env python3
"""
Inspection Bot — Front Steering 4WD keyboard controller.

Front wheels (fl, fr) steer via Ackermann geometry.
Rear wheels (rl, rr) stay straight, all four driven.

Publishes (Float64MultiArray, order = [fl, fr, rl, rr]):
  /steering_controller/commands   — 4 position values (rad)
  /drive_controller/commands      — 4 velocity values (rad/s)
"""

import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import sys
import termios
import tty
import select

# ── Vehicle geometry ──
WHEELBASE   = 0.460   # distance front axle to rear axle
TRACK_WIDTH = 0.476   # distance left wheel to right wheel

# ── Control limits ──
MAX_STEER  = 0.60     # rad (~34 deg), max front steering angle
STEP_STEER = 0.05     # rad per keypress
MAX_SPEED  = 12.0     # rad/s, max wheel velocity
STEP_SPEED = 1.0      # rad/s per keypress
PUB_RATE   = 0.05     # seconds

HELP_MSG = """
╔══════════════════════════════════════════════════════════════╗
║   Inspection Bot — Front Steering 4WD Mode                  ║
╠══════════════════════════════════════════════════════════════╣
║  W / S       : forward / reverse                            ║
║  A / D       : front steering left / right                  ║
║  SPACE or X  : stop and center steering                     ║
║  Q / E / Z / C : disabled                                   ║
║  ESC         : quit                                         ║
╚══════════════════════════════════════════════════════════════╝
"""

settings = None


def ackermann(steer):
    """Compute Ackermann front steering angles.

    steer > 0 -> left turn:  fl (inner) > fr (outer), both positive.
    steer < 0 -> right turn: fr (inner) more negative than fl (outer).
    steer = 0 -> straight.
    Returns (fl_angle, fr_angle).
    """
    if abs(steer) < 1e-9:
        return 0.0, 0.0

    R = WHEELBASE / math.tan(abs(steer))
    half_track = TRACK_WIDTH / 2.0

    if steer > 0:
        # left turn
        fl = math.atan(WHEELBASE / (R - half_track))
        fr = math.atan(WHEELBASE / (R + half_track))
    else:
        # right turn
        fl = -math.atan(WHEELBASE / (R + half_track))
        fr = -math.atan(WHEELBASE / (R - half_track))

    return fl, fr


def get_key():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = rlist[0].read(1) if rlist else ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class KeyboardController(Node):
    def __init__(self):
        super().__init__("keyboard_controller")

        self.pub_steering = self.create_publisher(
            Float64MultiArray, "/steering_controller/commands", 10
        )
        self.pub_drive = self.create_publisher(
            Float64MultiArray, "/drive_controller/commands", 10
        )

        self.speed = 0.0
        self.steer = 0.0   # virtual front steering angle (Ackermann reference)

        self.timer = self.create_timer(PUB_RATE, self.publish_commands)

    def publish_commands(self):
        fl, fr = ackermann(self.steer)

        # Steering: front wheels steer, rear stay straight
        steer_msg = Float64MultiArray()
        steer_msg.data = [fl, fr, 0.0, 0.0]
        self.pub_steering.publish(steer_msg)

        # Drive: all four wheels same speed
        drive_msg = Float64MultiArray()
        drive_msg.data = [self.speed] * 4
        self.pub_drive.publish(drive_msg)

        print(
            f"\r  speed: {self.speed:+7.2f} rad/s | steer: {self.steer:+7.2f} rad"
            f"  fl={fl:+7.3f} fr={fr:+7.3f} rl=0.000 rr=0.000  ",
            end="", flush=True,
        )


def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = KeyboardController()
    print(HELP_MSG)

    try:
        while rclpy.ok():
            key = get_key()

            if key == "w":
                node.speed = min(MAX_SPEED, node.speed + STEP_SPEED)
            elif key == "s":
                node.speed = max(-MAX_SPEED, node.speed - STEP_SPEED)
            elif key == "a":
                node.steer = min(MAX_STEER, node.steer + STEP_STEER)
            elif key == "d":
                node.steer = max(-MAX_STEER, node.steer - STEP_STEER)
            elif key in (" ", "x"):
                node.speed = 0.0
                node.steer = 0.0
                print("\n*** STOP + CENTER ***")
            elif key in ("q", "e", "z", "c"):
                print("\n  Crab/spot mode disabled in normal front-steer mode.")
            elif key in ("\x1b", "\x03"):
                break

            rclpy.spin_once(node, timeout_sec=0.01)

    except Exception as e:
        print(f"\nError: {e}")
    finally:
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
