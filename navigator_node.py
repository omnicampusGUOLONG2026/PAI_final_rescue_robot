#!/usr/bin/env python3
"""
Navigator Node (ROS 2 Humble / Nav2)
------------------------------------
- Listens to /navigation_goal_trigger from FallLogicNode.
- Sends navigation goals to ROS 2 Nav2 stack (Bedside Waypoint).
- Includes fail-safe rotation to face patient upon arrival.

Submission Account: omnicampusGUOLONG2026
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
import math


class NavigatorNode(Node):
    def __init__(self):
        super().__init__('navigator_node')

        # Subscriber for rescue navigation trigger
        self.trigger_sub = self.create_subscription(
            String,
            '/navigation_goal_trigger',
            self.trigger_callback,
            10
        )

        # Publisher for direct velocity control (fail-safe / fallback)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Nav2 Action Client
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Target Waypoint Configuration (Patient Bedside in Gazebo Hospital World)
        self.target_x = 2.5
        self.target_y = -1.2
        self.target_yaw = 0.0  # Orient towards patient bed

        self.get_logger().info('Navigator Node initialized and waiting for trigger...')

    def trigger_callback(self, msg: String):
        if msg.data == "START_NAVIGATION":
            self.get_logger().info('Rescue navigation triggered! Dispatching robot to bedside...')
            self.send_nav2_goal(self.target_x, self.target_y, self.target_yaw)

    def send_nav2_goal(self, x: float, y: float, yaw: float):
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn('Nav2 Action Server not available! Executing fallback direct drive...')
            self.execute_fallback_drive()
            return

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.position.z = 0.0

        # Convert Yaw to Quaternion
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        goal_pose.pose.orientation.z = sy
        goal_pose.pose.orientation.w = cy

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose

        self.get_logger().info(f'Sending Nav2 goal -> x: {x}, y: {y}, yaw: {yaw}')
        send_goal_future = self.nav_to_pose_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal was rejected by Nav2 server.')
            return

        self.get_logger().info('Goal accepted by Nav2. Moving to target...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result()
        self.get_logger().info(f'Arrival confirmed! Executing fail-safe rotation to face patient...')
        self.face_patient_rotation()

    def execute_fallback_drive(self):
        """Fail-safe direct command velocity publish when Nav2 is unavailable"""
        twist = Twist()
        twist.linear.x = 0.3
        twist.angular.z = 0.0
        for _ in range(20):
            self.cmd_vel_pub.publish(twist)

        # Stop and rotate
        twist.linear.x = 0.0
        twist.angular.z = 0.5
        for _ in range(10):
            self.cmd_vel_pub.publish(twist)

        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)

    def face_patient_rotation(self):
        """Rotate on spot to face patient and wait"""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.5
        for _ in range(12):
            self.cmd_vel_pub.publish(twist)
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        self.get_logger().info('Robot stationed at bedside. Alert active.')


def main(args=None):
    rclpy.init(args=args)
    node = NavigatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
