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
        
        # 1. 搬运 launch 文件夹里的 .launch.py 文件
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # 2. 搬运 urdf 文件夹里的所有文件
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        
        # 3. 搬运 meshes 文件夹里的所有文件 (STL模型)
        (os.path.join('share', package_name, 'meshes'), glob('meshes/*')),
        
        # 👇👇👇【关键修复】搬运 config 文件夹里的所有文件 👇👇👇
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wzc',
    maintainer_email='wzc@todo.todo',
    description='Inspection Bot Description Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)