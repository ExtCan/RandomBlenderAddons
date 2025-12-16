# CMakeLists.txt for Blender Internal Render Engine Translation Layer
#
# This builds the original Blender 2.79 render engine as a shared library
# that can be loaded by modern Blender through Python bindings.

cmake_minimum_required(VERSION 3.10)
project(blender_internal_render_engine C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Find Blender installation or source
# User should set BLENDER_INCLUDE_DIR to point to Blender's include directory
if(NOT DEFINED BLENDER_INCLUDE_DIR)
    message(FATAL_ERROR "BLENDER_INCLUDE_DIR must be set to Blender's include directory")
endif()

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/render/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/compat
    ${BLENDER_INCLUDE_DIR}
    ${Python3_INCLUDE_DIRS}
)

# Compatibility layer source files
set(COMPAT_SOURCES
    compat/blender_compat.c
    compat/api_translation.c
    compat/rna_bridge.c
    compat/dna_bridge.c
)

# Original render engine source files
file(GLOB RENDER_SOURCES 
    "render/source/*.c"
)

file(GLOB RAYTRACE_SOURCES
    "render/raytrace/*.cpp"
)

# Python binding
set(BINDING_SOURCES
    bindings/render_engine_module.c
)

# Create the Python extension module
Python3_add_library(blender_render_engine MODULE
    ${COMPAT_SOURCES}
    ${RENDER_SOURCES}
    ${RAYTRACE_SOURCES}
    ${BINDING_SOURCES}
)

target_link_libraries(blender_render_engine PRIVATE
    ${Python3_LIBRARIES}
)

# Set output name (without lib prefix on Unix)
set_target_properties(blender_render_engine PROPERTIES
    PREFIX ""
    OUTPUT_NAME "blender_render_engine"
)

# Installation
install(TARGETS blender_render_engine
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}
)

# Print configuration
message(STATUS "===========================================")
message(STATUS "Blender Internal Render Engine Build Configuration")
message(STATUS "===========================================")
message(STATUS "Python Include: ${Python3_INCLUDE_DIRS}")
message(STATUS "Python Libraries: ${Python3_LIBRARIES}")
message(STATUS "Blender Include: ${BLENDER_INCLUDE_DIR}")
message(STATUS "===========================================")
