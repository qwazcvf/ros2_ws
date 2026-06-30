#!/bin/bash

# 🛑 设置安全陷阱：按 Ctrl+C 时，把底层相机和翻转节点一起干掉！
trap "echo '🛑 接收到退出指令，正在安全关闭摄像头和翻转程序...'; kill $CAMERA_PID $FLIP_PID; exit" SIGINT SIGTERM

echo "========================================="
echo "👀 终极视觉系统启动中..."
echo "========================================="

# 🌍 刷新环境变量
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# 📷 1. 在后台启动底层的 USB 摄像头节点
echo "🚀 1. 正在唤醒 USB 摄像头底层驱动 (分辨率: 640x480)..."
ros2 run v4l2_camera v4l2_camera_node --ros-args -p image_size:="[640,480]" &
CAMERA_PID=$!  # 记住相机的进程编号

# ⏳ 给相机留 2 秒钟的开机预热时间
sleep 2

# 🔄 2. 在后台启动画面翻转魔法节点
echo "🔄 2. 正在启动画面翻转节点 (解决倒装问题)..."
python3 ~/ros2_ws/flip_camera.py &
FLIP_PID=$!  # 记住翻转程序的进程编号

echo "========================================="
echo "✅ 摄像头已完美起飞！"
echo "📺 请在 RViz 的 Image 插件中将 Topic 修改为: /image_flipped"
echo "🛑 想要关闭摄像头，请在此终端按下 Ctrl + C"
echo "========================================="

# 挂起脚本，让它在这里安静地守卫着这两个后台程序
wait
