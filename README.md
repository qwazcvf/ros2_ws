#------------------开启雷达---------------------------------
#1.检查串口
ls /dev/ttyACM*
#2.给权限
sudo chmod 777 /dev/ttyACM0
#4.检查验证硬件连接
/usr/local/bin/example_lidar_serial
#5.回到工作空间
cd ~/ros2_ws
source install/setup.bash
#6.启动
ros2 launch unitree_lidar_ros2 launch.py
#----------------------------------------------------------
