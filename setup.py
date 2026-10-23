from setuptools import find_packages, setup

package_name = 'PAI_final_rescue_robot'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='omnicampusGUOLONG2026',
    maintainer_email='omnicampusGUOLONG2026@user.noreply.github.com',
    description='AI Fall Detection and Autonomous Rescue Robot Navigation System',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vision_ai_node = PAI_final_rescue_robot.vision_ai_node:main',
            'fall_logic_node = PAI_final_rescue_robot.fall_logic_node:main',
            'navigator_node = PAI_final_rescue_robot.navigator_node:main',
        ],
    },
)
