#!/bin/bash

# ============================================================
# 🗺️ FAST-LIO 建图脚本
# 只跑 3D SLAM，2D 地图由 start_map_builder.sh 单独启动
# ============================================================

trap "echo '🛑 正在关闭...'; kill $SLAM_PID 2>/dev/null; exit" SIGINT SIGTERM

echo "========================================="
echo "🌍 加载 ROS2 环境..."
echo "========================================="

source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

echo ""
echo "========================================="
echo "🚀 启动 FAST-LIO 3D SLAM..."
echo "========================================="

ros2 launch fast_lio mapping.launch.py config_file:=unilidar_l2.yaml &
SLAM_PID=$!

echo "⏳ 等待 SLAM 初始化（3 秒）..."
sleep 3

echo ""
echo "✅ FAST-LIO 已启动，输出话题:"
echo "   /cloud_registered  ← 全局配准点云"
echo "   /path              ← 轨迹"
echo "   现在可以启动 start_map_builder.sh 生成 2D 地图"
echo ""
echo "🛑 按 Ctrl+C 退出"

wait $SLAM_PID
