#!/usr/bin/env python
import sys
from sensor_msgs.msg import Image
from fiducial_msgs.msg import FiducialArray, FiducialTransform, FiducialTransformArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import rospy
import numpy as np
from dynamic_reconfigure.server import Server
from data_base_recorder.cfg import RecorderConfig

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
        # self.dummy_c = rospy.Subscriber("/fiducial_transforms", FiducialTransformArray, self.transforms, queue_size=1)
        self.cfg_server = Server(RecorderConfig, self.server_cfg_callback)
        self.bl_id = 8
        self.br_id = 5
        self.tr_id = 6
        self.tl_id = 7
        self.calibrate = True
        self.t_matrix = np.zeros((3, 3), dtype=np.float32)
        self.maxWidth = 0.
        self.maxHeight = 0.

        # lower left:5, lower right:6, upper left:7, upper right:8
        self.corners = dict([
            (5, Corners(0, 0, 0, 0, 0)),
            (6, Corners(0, 0, 0, 0, 0)),
            (7, Corners(0, 0, 0, 0, 0)),
            (8, Corners(0, 0, 0, 0, 0)),
            (9, Corners(0, 0, 0, 0, 0))
            ])

    def server_cfg_callback(self, config, level):
        self.bl_id = config["bl"]
        self.br_id = config["br"]
        self.tr_id = config["tr"]
        self.tl_id = config["tl"]
        self.calibrate = config["calibrate"]
        return config

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

        if self.calibrate:
            # fu setup tl: 8, tr:6, br:7, bl:5
            tl = corners[self.tl_id]
            tr = corners[self.tr_id]
            br = corners[self.br_id]
            bl = corners[self.bl_id]

            pts1 = np.array([[tl.ix, tl.iy], [tr.ix, tr.iy], [br.ix, br.iy], [bl.ix, bl.iy]], dtype="float32")

            widthA = br.ix - bl.ix
            widthB = tr.ix - tl.ix
            self.maxWidth = max(int(widthA), int(widthB))
            heightA = br.iy - tr.iy
            heightB = bl.iy - tl.iy
            self.maxHeight = max(int(heightA), int(heightB))

            pts2 = np.array([
                [0, 0],
                [self.maxWidth, 0],
                [self.maxWidth, self.maxHeight],
                [0, self.maxHeight]], dtype="float32")

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
            self.t_matrix = cv2.getPerspectiveTransform(pts1, pts2)

        warped = cv2.warpPerspective(image, self.t_matrix, (self.maxWidth, self.maxHeight))

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
