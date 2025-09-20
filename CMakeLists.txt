cmake_minimum_required(VERSION 3.15)
project(mumeparrot_backtest)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)
find_package(Protobuf REQUIRED)
find_package(nlohmann_json REQUIRED)

# Find protoc compiler
if(NOT DEFINED Protobuf_PROTOC_EXECUTABLE)
    find_program(Protobuf_PROTOC_EXECUTABLE protoc)
endif()

if(NOT Protobuf_PROTOC_EXECUTABLE)
    message(FATAL_ERROR "protoc not found")
endif()

# Find gRPC plugin
find_program(gRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)
if(NOT gRPC_CPP_PLUGIN_EXECUTABLE)
    message(FATAL_ERROR "grpc_cpp_plugin not found")
endif()

# Find gRPC libraries
find_library(GRPC_LIBRARY grpc++)
find_library(GRPC_GRPC_LIBRARY grpc)
find_library(GPR_LIBRARY gpr)
if(NOT GRPC_LIBRARY OR NOT GRPC_GRPC_LIBRARY OR NOT GPR_LIBRARY)
    message(FATAL_ERROR "gRPC libraries not found")
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Generate protobuf and gRPC files
set(PROTO_PATH "${CMAKE_CURRENT_SOURCE_DIR}/protos")
set(BACKTEST_PROTO "${PROTO_PATH}/backtest.proto")
set(GENERATED_PROTOBUF_PATH "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(MAKE_DIRECTORY ${GENERATED_PROTOBUF_PATH})

set(BACKTEST_PB_CPP_FILE "${GENERATED_PROTOBUF_PATH}/backtest.pb.cc")
set(BACKTEST_PB_H_FILE "${GENERATED_PROTOBUF_PATH}/backtest.pb.h")
set(BACKTEST_GRPC_PB_CPP_FILE "${GENERATED_PROTOBUF_PATH}/backtest.grpc.pb.cc")
set(BACKTEST_GRPC_PB_H_FILE "${GENERATED_PROTOBUF_PATH}/backtest.grpc.pb.h")

add_custom_command(
    OUTPUT "${BACKTEST_PB_CPP_FILE}" "${BACKTEST_PB_H_FILE}" "${BACKTEST_GRPC_PB_CPP_FILE}" "${BACKTEST_GRPC_PB_H_FILE}"
    COMMAND ${Protobuf_PROTOC_EXECUTABLE}
    ARGS --grpc_out "${GENERATED_PROTOBUF_PATH}"
         --cpp_out "${GENERATED_PROTOBUF_PATH}"
         -I "${PROTO_PATH}"
         --plugin=protoc-gen-grpc="${gRPC_CPP_PLUGIN_EXECUTABLE}"
         "${BACKTEST_PROTO}"
    DEPENDS "${BACKTEST_PROTO}"
)

include_directories("${GENERATED_PROTOBUF_PATH}")

# Core library sources
set(CORE_SOURCES
    src/const.cpp
    src/configs.cpp
    src/data.cpp
    src/env.cpp
    src/sim.cpp
    src/full.cpp
    src/test.cpp
)

# Create core library
add_library(mumeparrot_core STATIC ${CORE_SOURCES})
target_link_libraries(mumeparrot_core 
    nlohmann_json::nlohmann_json
)

# Backtest executable
add_executable(backtest 
    backtest.cpp
)
target_link_libraries(backtest mumeparrot_core)

# Server executable
add_executable(server 
    server.cpp
    ${BACKTEST_PB_CPP_FILE}
    ${BACKTEST_GRPC_PB_CPP_FILE}
)
target_link_libraries(server 
    mumeparrot_core
    ${GRPC_LIBRARY}
    ${GRPC_GRPC_LIBRARY}
    ${GPR_LIBRARY}
    ${Protobuf_LIBRARIES}
    absl_synchronization
    absl_strings
    absl_base
)

# Optimize executable (port of optimize.py)
add_executable(optimize
    optimize.cpp
)
target_link_libraries(optimize mumeparrot_core)

# Install targets
install(TARGETS backtest server optimize
    RUNTIME DESTINATION bin
)

# Copy data files
file(GLOB CHART_FILES "${CMAKE_CURRENT_SOURCE_DIR}/charts/*")
file(GLOB INDEX_FILES "${CMAKE_CURRENT_SOURCE_DIR}/indices/*")

install(FILES 
    "${CMAKE_CURRENT_SOURCE_DIR}/tickers.json"
    "${CMAKE_CURRENT_SOURCE_DIR}/configs.json"
    DESTINATION .
)

if(CHART_FILES)
    install(FILES ${CHART_FILES} DESTINATION charts)
endif()

if(INDEX_FILES)
    install(FILES ${INDEX_FILES} DESTINATION indices)
endif()
