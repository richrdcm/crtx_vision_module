# CMake generated Testfile for 
# Source directory: /opt/crtx_vision_module/src/crtx_vision_module/fiducials/aruco_detect
# Build directory: /opt/crtx_vision_module/build/aruco_detect
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(_ctest_aruco_detect_rostest_test_aruco_images.test "/opt/crtx_vision_module/build/aruco_detect/catkin_generated/env_cached.sh" "/usr/bin/python2" "/opt/ros/melodic/share/catkin/cmake/test/run_tests.py" "/opt/crtx_vision_module/build/aruco_detect/test_results/aruco_detect/rostest-test_aruco_images.xml" "--return-code" "/usr/bin/python2 /opt/ros/melodic/share/rostest/cmake/../../../bin/rostest --pkgdir=/opt/crtx_vision_module/src/crtx_vision_module/fiducials/aruco_detect --package=aruco_detect --results-filename test_aruco_images.xml --results-base-dir \"/opt/crtx_vision_module/build/aruco_detect/test_results\" /opt/crtx_vision_module/src/crtx_vision_module/fiducials/aruco_detect/test/aruco_images.test ")
subdirs("gtest")
