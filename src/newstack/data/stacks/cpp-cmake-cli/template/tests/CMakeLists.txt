add_executable(test_counters test_counters.cpp)
target_link_libraries(test_counters PRIVATE textstat)

add_executable(test_options test_options.cpp)
target_link_libraries(test_options PRIVATE textstat)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(test_counters PRIVATE -Wall -Wextra -Wpedantic)
  target_compile_options(test_options PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_test(NAME counters COMMAND test_counters)
add_test(NAME options COMMAND test_options)

# Drives the real executable: usage output and exit codes are part of the contract.
add_test(
  NAME cli
  COMMAND ${CMAKE_COMMAND}
          -DEXE=$<TARGET_FILE:${PROJECT_NAME}>
          -DINPUT=${CMAKE_CURRENT_SOURCE_DIR}/data/sample.txt
          -P ${CMAKE_CURRENT_SOURCE_DIR}/cli_tests.cmake)
