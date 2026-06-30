#!/bin/bash

# ============================================================
# 🚀 雷达启动脚本（UDP 网口模式）
# 硬件：Unitree L2 LiDAR ↔ Jetson enP8p1s0 直连
# ============================================================

echo "========================================="
echo "🔍 1. 检查网口连接状态..."
echo "========================================="

# 检查网口物理链路
LINK_STATE=$(ip link show enP8p1s0 2>/dev/null | grep -oP 'state \K\w+')
if [ "$LINK_STATE" != "UP" ]; then
    echo "❌ 错误：网口 enP8p1s0 未连接！请检查网线。"
    exit 1
fi
echo "✅ 网口 enP8p1s0 物理链路正常"

# 检查并配置 IP
CURRENT_IP=$(ip addr show enP8p1s0 | grep -oP 'inet \K[\d.]+')
if [ "$CURRENT_IP" != "192.168.1.2" ]; then
    echo "⚙️  正在配置 Jetson 网口 IP: 192.168.1.2/24 ..."
    # 如果有旧 IP 先删掉
    if [ -n "$CURRENT_IP" ]; then
        sudo ip addr del ${CURRENT_IP}/24 dev enP8p1s0 2>/dev/null
    fi
    sudo ip addr add 192.168.1.2/24 dev enP8p1s0
    echo "✅ IP 已配置为 192.168.1.2"
else
    echo "✅ IP 已是 192.168.1.2，无需重新配置"
fi

echo ""
echo "========================================="
echo "📡 2. 加载 ROS2 环境..."
echo "========================================="

source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# 杀掉残留的雷达进程，释放 UDP 端口
echo "🧹 清理残留雷达进程..."
pkill -f unitree_lidar_ros2_node 2>/dev/null
sleep 1

echo ""
echo "========================================="
echo "🚀 3. 启动雷达节点 (UDP 模式)..."
echo "   雷达 IP: 192.168.1.62:6101"
echo "   Jetson:  192.168.1.2:6201"
echo "========================================="

ros2 launch unitree_lidar_ros2 launch.py
