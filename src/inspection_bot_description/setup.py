from setuptools import setup
import os
from glob import glob

package_name = 'inspection_bot_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # Launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),

        # URDF / xacro files (glob('urdf/*') catches .urdf, .xacro, .csv)
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),

        # Meshes (STL models — kept for future use)
        (os.path.join('share', package_name, 'meshes'), glob('meshes/*')),

        # Controller configuration
        (os.path.join('share', package_name, 'config'), glob('config/*')),

        # RViz configuration
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),

        # Gazebo worlds
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wzc',
    maintainer_email='wzc@todo.todo',
    description='Inspection Bot — 4-wheel independent steering robot description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'keyboard_control = inspection_bot_description.keyboard_control:main',
            'static_joint_state_publisher = inspection_bot_description.static_joint_state_publisher:main',
        ],
    },
)