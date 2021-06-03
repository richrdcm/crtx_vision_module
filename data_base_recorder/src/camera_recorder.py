#!/usr/bin/env python
import sys
import rospy
from sensor_msgs.msg import Image
from fiducial_msgs.msg import FiducialArray, FiducialTransform, FiducialTransformArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import rospy

class camera_recorder:

    def __init__(self):
        self.bridge = CvBridge()
        self.image_pub_result = rospy.Publisher("/camera_recorder/image", Image, queue_size=1)
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, self.image, queue_size=1)
        self.image_sub = rospy.Subscriber("/fiducial_vertices", FiducialArray, self.markers, queue_size=1)
        self.record = False
        self.last_time = rospy.Time.now()
        self.corner_5 = (0, 0)
        self.corner_6 = (0, 0)
        self.corner_7 = (0, 0)
        self.corner_8 = (0, 0)
        self.corners_ids = [5, 6, 7, 8]

    def image(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)


        # transformation
        gray=cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        dt = (rospy.Time.now() - self.last_time).to_sec()
        #print("dt: {}".format(dt))
        if (dt > 0.5):
            self.record = True

        try:
            if self.record:
                self.image_pub_result.publish(self.bridge.cv2_to_imgmsg(gray, "mono8"))
        except CvBridgeError as e:
            print(e)

    def markers(self, data):

        for i in range(len(data.fiducials)):
            transformation = data.fiducials[i]
            id = transformation.fiducial_id
            # print("id: {}".format(id))
            cx = transformation.x0 + (transformation.x2 - transformation.x0)
            cy = transformation.y0 + (transformation.y2 - transformation.y0)
            if id == 5:
                self.corner_5 = (cx, cy)
                self.last_time = rospy.Time.now()
                self.record = False
            elif id == 6:
                self.corner_6 = (cx, cy)
            elif id == 7:
                self.corner_7 = (cx, cy)
            elif id == 8:
                self.corner_8 = (cx, cy)






def main(args):
    rospy.init_node('camera_recorder', anonymous=True)
    ic = camera_recorder()

    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
#  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)