cmake_minimum_required(VERSION 2.8.3)
project(human_console)

find_package(catkin REQUIRED COMPONENTS
  roslib
  rospy
  roscpp
  std_msgs
  message_generation
  cmake_modules
  wam_control
  pluginlib
)

#find_package(Eigen REQUIRED)

catkin_python_setup()

#generate_messages(
#  DEPENDENCIES
#)


catkin_package(
  #INCLUDE_DIRS include
  #  LIBRARIES human_console
  CATKIN_DEPENDS message_runtime
  #  DEPENDS system_lib
)


include_directories(
  include
  ${catkin_INCLUDE_DIRS}
  ${Eigen_INCLUDE_DIRS}
)

install(FILES plugin.xml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY resource
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(PROGRAMS 
  scripts/udp_gui
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)