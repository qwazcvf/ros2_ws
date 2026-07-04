from setuptools import setup
import os
from glob import glob

package_name = 'inspection_bot_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'models', 'inspection_bot'), glob('models/inspection_bot/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wzc',
    maintainer_email='wzc@todo.todo',
    description='Inspection Bot Simulation — Gazebo world, virtual sensors, RViz',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
        ],
    },
)
