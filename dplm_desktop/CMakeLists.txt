macro(print_all_variables)
    message(STATUS "print_all_variables------------------------------------------{")
    get_cmake_property(_variableNames VARIABLES)
    foreach (_variableName ${_variableNames})
        message(STATUS "${_variableName}=${${_variableName}}")
    endforeach()
    message(STATUS "print_all_variables------------------------------------------}")
endmacro()


cmake_minimum_required(VERSION 3.5)


project(DPLM VERSION 0.1)


set(CMAKE_FIND_LIBRARY_SUFFIXES ".a" ".dll")
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

ADD_DEFINITIONS(-DQT_NO_KEYWORDS)

find_package(Python COMPONENTS Interpreter Development REQUIRED)
message("Python_FOUND:${Python_FOUND}")
message("Python_VERSION:${Python_VERSION}")
message("Python_Development_FOUND:${Python_Development_FOUND}")
message("Python_LIBRARIES:${Python_LIBRARIES}")
message("Python_STDLIB:${Python_STDLIB}")
message("Python_STDARCH:${Python_STDARCH}")


set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(QT NAMES Qt5 COMPONENTS Widgets REQUIRED)
find_package(Qt5 COMPONENTS Widgets REQUIRED)
find_package(OpenSSL 1.1 REQUIRED)

set(PROJECT_SOURCES
    python_utilities.h
    dplm.h dplm.cpp
    dplm.ui login.ui endpointForm.ui writeForm.ui
    httpRequest.hpp httpRequest.cpp
    main.cpp
    web_client.hpp
    plotSensor.py
)

if(${QT_VERSION_MAJOR} GREATER_EQUAL 6)
    qt_add_executable(DPLM
        MANUAL_FINALIZATION
        ${PROJECT_SOURCES}
    )
else()
    if(ANDROID)
        add_library(DPLM SHARED
            ${PROJECT_SOURCES}
        )
    else()
        add_executable(DPLM
            ${PROJECT_SOURCES}
        )
    endif()
endif()


if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(DPLM)
endif()


### helper to find package variables
#print_all_variables()

target_include_directories(DPLM
    PRIVATE ${Python_INCLUDE_DIRS}
    cpp-httplib
)

link_directories(
    ${CMAKE_SOURCE_DIR}
)
target_link_libraries(DPLM
    PRIVATE ${Python_LIBRARIES}
    Qt5::Widgets
    cryptopp
    OpenSSL::SSL
    crypto
    ws2_32
    crypt32
)


