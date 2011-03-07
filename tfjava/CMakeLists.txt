cmake_minimum_required(VERSION 2.4.6)
include($ENV{ROS_ROOT}/core/rosbuild/rosbuild.cmake)

rosbuild_init()

#######################################

set(EXECUTABLE_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/bin)
set(LIBRARY_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/lib)
set(JAVA_OUTPUT_DIR ${PROJECT_SOURCE_DIR}/bin)

add_classpath(${PROJECT_SOURCE_DIR}/lib/vecmath.jar)
add_runtime_classpath(${PROJECT_SOURCE_DIR}/lib/vecmath.jar)

add_java_source_dir(${PROJECT_SOURCE_DIR}/src)
