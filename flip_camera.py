#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class ImageFlipper(Node):
    def __init__(self):
        super().__init__('image_flipper_node')
        # 1. 订阅原始倒着的画面
        self.sub = self.create_subscription(Image, '/image_raw', self.img_callback, 10)
        # 2. 发布翻转后的正向画面
        self.pub = self.create_publisher(Image, '/image_flipped', 10)
        self.bridge = CvBridge()
        self.get_logger().info("🔄 图像翻转魔法节点已启动！正在输出到 /image_flipped")

    def img_callback(self, msg):
        try:
            # 将 ROS 图像转为 OpenCV 格式
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # cv2.flip() 的参数: 0 是上下翻转，1 是左右翻转，-1 是上下+左右都翻转 (即旋转180度)
            # 因为摄像头是倒着装的，所以我们需要上下左右全翻转，相当于把它转 180 度！
            flipped_img = cv2.flip(cv_img, -1)
            
            # 转回 ROS 格式并发布
            new_msg = self.bridge.cv2_to_imgmsg(flipped_img, encoding='bgr8')
            new_msg.header = msg.header  # 保持时间戳和坐标系不变
            self.pub.publish(new_msg)
        except Exception as e:
            self.get_logger().error(f"图像处理报错: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ImageFlipper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
