#!/usr/bin/env python
import sys
import rospy
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


class CameraRecorder:

    def __init__(self):
        self.bridge = CvBridge()
        self.image_pub_result = rospy.Publisher("/camera_recorder/image", Image, queue_size=1)
        self.dummy_a = rospy.Subscriber("/usb_cam/image_raw", Image, self.image, queue_size=1)
        self.dummy_b = rospy.Subscriber("/fiducial_vertices", FiducialArray, self.markers, queue_size=1)
        self.dummy_c = rospy.Subscriber("/fiducial_transforms", FiducialTransformArray, self.transforms, queue_size=1)
        self.record = False
        self.last_time = rospy.Time.now()
        # lower left:5, lower right:6, upper left:7, upper right:8
        self.corners = dict([
            (5, Corners(0, 0, 0, 0, 0)),
            (6, Corners(0, 0, 0, 0, 0)),
            (7, Corners(0, 0, 0, 0, 0)),
            (8, Corners(0, 0, 0, 0, 0))
            ])

    def image(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)

        # transformation
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        warped = self.perspective_transform(cv_image, self.corners)

        dt = (rospy.Time.now() - self.last_time).to_sec()
        # print("dt: {}".format(dt))
        if (dt > 0.5):
            self.record = True
        # cv2.imshow("aqui",warped)
        # cv2.waitKey(0)
        self.image_pub_result.publish(self.bridge.cv2_to_imgmsg(warped, "bgr8"))

        # try:
        #     if self.record:
        #         self.image_pub_result.publish(self.bridge.cv2_to_imgmsg(warped, "bgr8"))
        # except CvBridgeError as e:
        #     print(e)

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
            if id == 9:
                self.last_time = rospy.Time.now()
                self.record = False

    def transforms(self, data):

        for i in range(len(data.transforms)):
            transformation = data.transforms[i]
            id = transformation.fiducial_id
            # print("id: {}".format(id))
            self.corners[id].tx = transformation.transform.translation.x
            self.corners[id].ty = transformation.transform.translation.y
            self.corners[id].tz = transformation.transform.translation.z

    def perspective_transform(self, image, corners):
        # compute the width of the new image, which will be the
        # maximum distance between bottom-right and bottom-left
        # x-coordiates or the top-right and top-left x-coordinates
        bl = corners[5] # 8
        br = corners[6] # 7
        tl = corners[8] # 5
        tr = corners[7]  # 6

        print("=" * 50)
        print(corners[5])
        print(corners[7])
        print(corners[6])
        print(corners[8])
        print("=" * 50)


        rect = np.zeros((4, 2), dtype="float32")
        rect_ = np.array([[tl.ix, tl.iy], [tr.ix, tr.iy],
                         [br.ix, br.iy], [bl.ix, bl.iy]])

        # rect_ = np.array([[tl.tx - tl.tx, tl.ty - tl.ty], [tr.tx - tl.tx, tr.ty - tl.ty],
        #                   [br.tx - tl.tx, br.ty - tl.ty], [bl.tx - tl.tx, bl.ty - tl.ty]])
        dst_ = np.array([[tl.ix, tl.iy], [tr.ix, tr.iy],
                         [br.ix, br.iy], [bl.ix, bl.iy]])

        s = rect_.sum(axis=1)
        rect[0] = rect_[np.argmin(s)]
        rect[2] = rect_[np.argmax(s)]
        diff = np.diff(rect_, axis=1)
        rect[1] = rect_[np.argmin(diff)]
        rect[3] = rect_[np.argmax(diff)]

        widthA = br.ix - bl.ix # np.sqrt(((br.ix - bl.ix) ** 2) + ((br.iy - bl.iy) ** 2))
        widthB = tr.ix - tl.ix # np.sqrt(((tr.ix - tl.ix) ** 2) + ((tr.iy - tl.iy) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        # compute the height of the new image, which will be the
        # maximum distance between the top-right and bottom-right
        # y-coordinates or the top-left and bottom-left y-coordinates
        heightA = tr.iy - br.iy # np.sqrt(((tr.ix - br.ix) ** 2) + ((tr.iy - br.iy) ** 2))
        heightB = tl.ix - bl.ix # np.sqrt(((tl.ix - bl.ix) ** 2) + ((tl.iy - bl.iy) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        # now that we have the dimensions of the new image, construct
        # the set of destination points to obtain a "birds eye view",
        # (i.e. top-down view) of the image, again specifying points
        # in the top-left, top-right, bottom-right, and bottom-left
        # order
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")

        # print("=" * 50)
        # print(rect_)
        # print(dst_)
        # print(rect)
        # print(dst)
        # print("=" * 50)
        # compute the perspective transform matrix and then apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))  # (maxWidth, maxHeight)
        # return the warped image
        return warped



def main(args):
    rospy.init_node('camera_recorder', anonymous=True)
    ic = CameraRecorder()

    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")


#  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
