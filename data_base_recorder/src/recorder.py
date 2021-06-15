#!/usr/bin/env python
import sys
import cv2
import rospy
from sensor_msgs.msg import Image
from fiducial_msgs.msg import FiducialArray, FiducialTransform, FiducialTransformArray
from cv_bridge import CvBridge, CvBridgeError
from datetime import date, datetime
from dynamic_reconfigure.server import Server
from data_base_recorder.cfg import RecorderConfig


class CameraRecorder:

    def __init__(self):
        self.bridge = CvBridge()
        self.topic_to_record = "/perspective_transformation/image"
        self.dummy_a = rospy.Subscriber(self.topic_to_record, Image, self.get_image, queue_size=1)
        self.dummy_b = rospy.Subscriber("/fiducial_vertices", FiducialArray, self.get_markers, queue_size=1)
        self.record = True
        self.dynamic_record = True
        self.last_time = rospy.Time.now()
        self.save_location = "/mnt/ameli/live_dataset"
        self.rec_id = 9
        self.cfg_server = Server(RecorderConfig, self.server_cfg_callback)


    def server_cfg_callback(self, config, level):
        rospy.loginfo("""Reconfigure Request: {save_location}, {start_recording},\ 
              {topic_to_record}""".format(**config))
        self.save_location = config["save_location"]
        self.dynamic_record = config["start_recording"]
        self.topic_to_record = config["topic_to_record"]
        self.dummy_a.unregister()
        self.rec_id = config["rec_marker"]
        self.dummy_a = rospy.Subscriber(self.topic_to_record, Image, self.get_image, queue_size=1)
        return config

    def get_image(self, image):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(image, "bgr8")
        except CvBridgeError as e:
            print(e)

        dt = (rospy.Time.now() - self.last_time).to_sec()
        if (dt > 0.5):
            self.record = True

        try:
            if self.record and self.dynamic_record:
                now = datetime.now()
                current_time = now.strftime("%H-%M-%S-%f")
                today = date.today().strftime("%Y-%m-%d")
                name = self.save_location + "/" + today + "-" + current_time + "-" + str(rospy.Time.now().nsecs) + ".jpg"
                cv2.imwrite(name, cv_image)
                rospy.loginfo("Recording frames...")
        except CvBridgeError as e:
            print(e)

    def get_markers(self, data):

        for i in range(len(data.fiducials)):
            transformation = data.fiducials[i]
            id = transformation.fiducial_id
            if id == self.rec_id:
                self.last_time = rospy.Time.now()
                self.record = False
                rospy.loginfo("Not recording frames...")



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