#!/usr/bin/env python3
"""
Inspection Bot — /cmd_vel Keyboard Control (Phase 2A).

Publishes ONLY /cmd_vel (geometry_msgs/msg/Twist).
Does NOT publish any controller command topics.

Controls:
  W / S       : forward / reverse
  A / D       : turn left / right
  SPACE / X   : stop
  Q/E/Z/C     : disabled
  ESC / Ctrl-C: quit
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty
import select

MAX_LINEAR  = 0.60    # m/s (real speed range 0.2~0.6)
MAX_REVERSE = 0.20    # m/s
MAX_ANGULAR = 1.50    # rad/s
STEP_LINEAR = 0.05    # m/s per keypress
STEP_ANGULAR = 0.10   # rad/s per keypress
PUB_RATE = 0.05       # 20 Hz

HELP_MSG = """
╔══════════════════════════════════════════════════════════════╗
║   Inspection Bot — /cmd_vel Keyboard Control (Phase 2A)     ║
╠══════════════════════════════════════════════════════════════╣
║  W / S       : forward / reverse                            ║
║  A / D       : turn left / right                            ║
║  SPACE or X  : stop                                         ║
║  Q / E / Z / C : disabled                                    ║
║  ESC / Ctrl-C : quit                                        ║
║                                                             ║
║  Publishes only: /cmd_vel                                   ║
║  Does not publish controller command topics                 ║
╚══════════════════════════════════════════════════════════════╝
"""

settings = None


def get_key():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = rlist[0].read(1) if rlist else ""
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


class KeyboardController(Node):
    def __init__(self):
        super().__init__("keyboard_control")
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.linear_x = 0.0
        self.angular_z = 0.0
        self.timer = self.create_timer(PUB_RATE, self.publish_cmd)

    def publish_cmd(self):
        msg = Twist()
        msg.linear.x = self.linear_x
        msg.angular.z = self.angular_z
        self.cmd_pub.publish(msg)
        print(f"\r  linear: {self.linear_x:+6.2f} m/s | angular: {self.angular_z:+6.2f} rad/s  ",
              end="", flush=True)


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
                node.linear_x = min(MAX_LINEAR, node.linear_x + STEP_LINEAR)
            elif key == "s":
                node.linear_x = max(-MAX_REVERSE, node.linear_x - STEP_LINEAR)
            elif key == "a":
                node.angular_z = min(MAX_ANGULAR, node.angular_z + STEP_ANGULAR)
            elif key == "d":
                node.angular_z = max(-MAX_ANGULAR, node.angular_z - STEP_ANGULAR)
            elif key in (" ", "x"):
                node.linear_x = 0.0
                node.angular_z = 0.0
                print("\n*** STOP ***")
            elif key in ("q", "e", "z", "c"):
                print("\n  Q/E/Z/C disabled. Use A/D for turning, W/S for speed.")
            elif key in ("\x1b", "\x03"):
                break
            rclpy.spin_once(node, timeout_sec=0.01)
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        zero = Twist()
        node.cmd_pub.publish(zero)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()
        print("\nController stopped.")


if __name__ == "__main__":
    main()
