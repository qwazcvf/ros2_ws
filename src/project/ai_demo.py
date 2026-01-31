import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge 
import cv2
from ultralytics import YOLO

class AiDetector(Node):
    def __init__(self):
        super().__init__('ai_detector_node')
        # 1. 订阅摄像头的画面
        self.subscription = self.create_subscription(
            Image,
            '/image_raw', 
            self.listener_callback,
            10)
        self.bridge = CvBridge()
        # 2. 加载 AI 模型 (第一次运行会自动下载)
        print("正在加载 AI 模型，请稍候...")
        self.model = YOLO("yolov8n.pt") 
        print("模型加载完毕！请把摄像头对准物体！")

    def listener_callback(self, msg):
        try:
            # 3. 格式转换：ROS图片 -> OpenCV图片
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # 4. AI 推理
            results = self.model(frame, verbose=False)
            
            # 5. 画框框
            annotated_frame = results[0].plot()
            
            # 6. 显示画面
            cv2.imshow("My AI Robot View", annotated_frame)
            cv2.waitKey(1)
            
        except Exception as e:
            print(f"出错了: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = AiDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()