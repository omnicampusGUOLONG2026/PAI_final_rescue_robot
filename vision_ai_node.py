import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO

class VisionAINode(Node):
    """
    Vision AI Node for detecting falls using YOLOv8-Pose estimation.
    Analyzes camera frames from hospital room and publishes fall candidate events.
    """
    def __init__(self):
        super().__init__('vision_ai_node')
        
        # Publishers and Subscribers
        self.publisher_ = self.create_publisher(String, '/fall_event', 10)
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        self.bridge = CvBridge()
        
        # Load YOLOv8-Pose model (Pre-trained keypoint estimation model)
        self.get_logger().info('Loading YOLOv8-Pose model...')
        self.model = YOLO('yolov8n-pose.pt')
        self.get_logger().info('Vision AI Node has been successfully initialized.')

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {str(e)}')
            return

        # Perform pose estimation
        results = self.model(cv_image, verbose=False)

        for result in results:
            if result.boxes is None or result.keypoints is None:
                continue

            # Analyze each detected person
            for box, kpts in zip(result.boxes, result.keypoints):
                # Calculate bounding box aspect ratio (width / height)
                xyxy = box.xyxy[0].cpu().numpy()
                width = xyxy[2] - xyxy[0]
                height = xyxy[3] - xyxy[1]
                
                if height <= 0:
                    continue
                
                aspect_ratio = width / height

                # Keypoints (17 COCO keypoints)
                # 5: Left Shoulder, 6: Right Shoulder, 11: Left Hip, 12: Right Hip
                keypoints = kpts.data[0].cpu().numpy()
                
                # Geometric logic for fall detection (Aspect ratio > 1.1)
                if aspect_ratio > 1.1:
                    event_msg = String()
                    event_msg.data = "DETECTED"
                    self.publisher_.publish(event_msg)
                    self.get_logger().info('Fall candidate detected by Vision AI Node.')
                    break

def main(args=None):
    rclpy.init(args=args)
    node = VisionAINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()