#!/usr/bin/env python
import sys
from sensor_msgs.msg import Image
from fiducial_msgs.msg import FiducialArray, FiducialTransform, FiducialTransformArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import rospy
import numpy as np


class Corners:
    def __init__(self, ix, iy, tx, ty, tz):
        self.ix = ix
        self.iy = iy
        self.tx = tx
        self.ty = ty
        self.tz = tz

    def __repr__(self):
        return "Corner ix:% s, iy:% s, tx:% s, ty:% s, tz:% s" % (self.ix, self.iy, self.tx, self.ty, self.tz)


class PerspectiveTransformation:

    def __init__(self):
        self.bridge = CvBridge()
        self.image_pub_result = rospy.Publisher("/perspective_transformation/image", Image, queue_size=1)
        self.dummy_a = rospy.Subscriber("/usb_cam/image_raw", Image, self.image, queue_size=1)
        self.dummy_b = rospy.Subscriber("/fiducial_vertices", FiducialArray, self.markers, queue_size=1)
        self.dummy_c = rospy.Subscriber("/fiducial_transforms", FiducialTransformArray, self.transforms, queue_size=1)

        # lower left:5, lower right:6, upper left:7, upper right:8
        self.corners = dict([
            (5, Corners(0, 0, 0, 0, 0)),
            (6, Corners(0, 0, 0, 0, 0)),
            (7, Corners(0, 0, 0, 0, 0)),
            (8, Corners(0, 0, 0, 0, 0)),
            (9, Corners(0, 0, 0, 0, 0))
            ])

    def image(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)

        # transformation
        warped = self.perspective_transform(cv_image, self.corners)
        self.image_pub_result.publish(self.bridge.cv2_to_imgmsg(warped, "bgr8"))

    def markers(self, data):

        for i in range(len(data.fiducials)):
            transformation = data.fiducials[i]
            id = transformation.fiducial_id
            # print("id: {}".format(id))
            x_min = min(transformation.x0, transformation.x1, transformation.x2, transformation.x3)
            x_max = max(transformation.x0, transformation.x1, transformation.x2, transformation.x3)
            y_min = min(transformation.y0, transformation.y1, transformation.y2, transformation.y3)
            y_max = max(transformation.y0, transformation.y1, transformation.y2, transformation.y3)
            cx = x_min + (x_max - x_min) / 2
            cy = y_min + (y_max - y_min) / 2
            self.corners[id].ix = cx
            self.corners[id].iy = cy


    def transforms(self, data):

        for i in range(len(data.transforms)):
            transformation = data.transforms[i]
            id = transformation.fiducial_id
            # print("id: {}".format(id))
            self.corners[id].tx = transformation.transform.translation.x
            self.corners[id].ty = transformation.transform.translation.y
            self.corners[id].tz = transformation.transform.translation.z

    def perspective_transform(self, image, corners):

        # fu setup tl: 8, tr:6, br:7, bl:5
        tl = corners[7]
        tr = corners[6]
        br = corners[5]
        bl = corners[8]

        pts1 = np.array([[tl.ix, tl.iy], [tr.ix, tr.iy], [br.ix, br.iy], [bl.ix, bl.iy]], dtype="float32")

        widthA = br.ix - bl.ix
        widthB = tr.ix - tl.ix
        maxWidth = max(int(widthA), int(widthB))
        heightA = br.iy - tr.iy
        heightB = bl.iy - tl.iy
        maxHeight = max(int(heightA), int(heightB))

        pts2 = np.array([
            [0, 0],
            [maxWidth, 0],
            [maxWidth, maxHeight],
            [0, maxHeight]], dtype="float32")

        # print("=" * 50)
        # print(tl)
        # print(tr)
        # print(br)
        # print(bl)
        # print("=" * 50)
        # print("=" * 50)
        # print(pts1)
        # print(pts2)
        # print("=" * 50)

        # compute the perspective transform matrix and then apply it
        M = cv2.getPerspectiveTransform(pts1, pts2)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        return warped

def main(args):
    rospy.init_node('camera_recorder', anonymous=True)
    ic = PerspectiveTransformation()

    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")


if __name__ == '__main__':
    main(sys.argv)
