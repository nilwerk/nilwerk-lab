# Host unit tests for the sensor drivers (task 4.F1). No ESP-IDF, no hardware: gcc/clang + cmake + python3.
# CI: cmake -S test/host -B build-host && cmake --build build-host && ctest --test-dir build-host --output-on-failure
cmake_minimum_required(VERSION 3.16)
project(nw_sensors_host C)
set(CMAKE_C_STANDARD 11)
set(SENS ${CMAKE_CURRENT_SOURCE_DIR}/../../components/sensors)
set(DRV ${SENS}/src/nw_aht20.c ${SENS}/src/nw_bh1750.c ${SENS}/src/nw_soil.c ${SENS}/src/nw_battery.c)
add_executable(test_sensors test_main.c ${DRV})
target_include_directories(test_sensors PRIVATE ${SENS}/include ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_options(test_sensors PRIVATE -Wall -Wextra -Werror)
if(NOT MSVC)
  target_compile_options(test_sensors PRIVATE -fsanitize=address,undefined -fno-sanitize-recover=undefined)
  target_link_options(test_sensors PRIVATE -fsanitize=address,undefined)
endif()
enable_testing()
add_test(NAME sensors_unit COMMAND test_sensors)
find_package(Python3 COMPONENTS Interpreter)
if(Python3_FOUND)
  add_test(NAME board_pins_cite_pinmap
           COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check_board_pins.py)
  add_test(NAME mutation_checks
           COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/mutate.py ${CMAKE_C_COMPILER})
endif()
