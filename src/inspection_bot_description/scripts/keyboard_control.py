#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import sys
import termios
import tty
import select  # <--- 之前漏了这个模块！

# ================= 配置参数 =================
MAX_SPEED = 20.0      # 最大速度 (rad/s)
MAX_STEER = 1.0       # 最大转向角 (rad, 约57度)
STEP_SPEED = 2.0      # 按一下 W/S 增加的速度
STEP_STEER = 0.1      # 按一下 A/D 增加的角度
# ===========================================

msg = """
--------------------------------------------
   Inspection Bot 键盘控制器 (阿克曼模式)
--------------------------------------------
   W: 加速
   S: 减速/倒车
   A: 左转 (前轮)
   D: 右转 (前轮)
   
   空格: 急刹车 & 回正
   Q:    退出
--------------------------------------------
"""

settings = None

def getKey():
    # 获取键盘按键，不回显
    tty.setraw(sys.stdin.fileno())
    # 👇👇👇 之前这里写错了，应该是 select.select 👇👇👇
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class KeyboardController(Node):
    def __init__(self):
        super().__init__('keyboard_controller')
        
        # 定义发布者
        self.pub_drive = self.create_publisher(Float64MultiArray, '/drive_controller/commands', 10)
        self.pub_front_steer = self.create_publisher(Float64MultiArray, '/front_steering_controller/commands', 10)
        self.pub_rear_steer = self.create_publisher(Float64MultiArray, '/rear_steering_controller/commands', 10)

        self.speed = 0.0
        self.steer = 0.0

    def publish_commands(self):
        # 1. 发送驱动指令 (4个轮子)
        drive_msg = Float64MultiArray()
        drive_msg.data = [self.speed, self.speed, self.speed, self.speed]
        self.pub_drive.publish(drive_msg)

        # 2. 发送前轮转向指令 (2个前轮)
        steer_msg = Float64MultiArray()
        steer_msg.data = [self.steer, self.steer]
        self.pub_front_steer.publish(steer_msg)

        # 3. 发送后轮指令 (锁死为0)
        rear_msg = Float64MultiArray()
        rear_msg.data = [0.0, 0.0]
        self.pub_rear_steer.publish(rear_msg)

        # 打印状态 (加了回车符，防止刷屏太乱)
        print(f"\r当前状态 -> 速度: {self.speed:.2f} | 转向角: {self.steer:.2f}   ", end="")

def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)
    
    rclpy.init()
    node = KeyboardController()
    
    print(msg)
    
    try:
        while True:
            key = getKey()
            if key == 'w':
                node.speed = min(MAX_SPEED, node.speed + STEP_SPEED)
            elif key == 's':
                node.speed = max(-MAX_SPEED, node.speed - STEP_SPEED)
            elif key == 'a':
                node.steer = min(MAX_STEER, node.steer + STEP_STEER)
            elif key == 'd':
                node.steer = max(-MAX_STEER, node.steer - STEP_STEER)
            elif key == ' ':
                node.speed = 0.0
                node.steer = 0.0
                print("\n*** 急刹车! ***")
            elif key == 'q':
                break
            
            # 只有按键或者循环时持续发布
            node.publish_commands()

    except Exception as e:
        print(e)

    finally:
        # 发送停止指令
        stop_msg = Float64MultiArray()
        stop_msg.data = [0.0, 0.0, 0.0, 0.0]
        node.pub_drive.publish(stop_msg)
        
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()