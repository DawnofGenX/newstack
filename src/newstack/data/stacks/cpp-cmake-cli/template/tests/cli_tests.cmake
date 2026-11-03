# Behavioural checks on the built executable, run by ctest:
#   cmake -DEXE=<binary> -DINPUT=<sample.txt> -P cli_tests.cmake

if(NOT DEFINED EXE OR NOT DEFINED INPUT)
  message(FATAL_ERROR "cli_tests.cmake needs -DEXE=<binary> and -DINPUT=<file>")
endif()

execute_process(
  COMMAND "${EXE}" --help
  OUTPUT_VARIABLE help_out
  ERROR_VARIABLE help_err
  RESULT_VARIABLE help_rc)
if(NOT help_rc EQUAL 0)
  message(FATAL_ERROR "--help exited ${help_rc}, expected 0 (stderr: ${help_err})")
endif()
if(NOT help_out MATCHES "usage:")
  message(FATAL_ERROR "--help printed no usage line:\n${help_out}")
endif()

execute_process(
  COMMAND "${EXE}" --definitely-not-a-flag
  OUTPUT_VARIABLE bad_out
  ERROR_VARIABLE bad_err
  RESULT_VARIABLE bad_rc)
if(NOT bad_rc EQUAL 2)
  message(FATAL_ERROR "unknown option exited ${bad_rc}, expected 2")
endif()
if(NOT bad_err MATCHES "unknown option")
  message(FATAL_ERROR "unknown option printed no diagnostic (stderr: '${bad_err}')")
endif()

execute_process(
  COMMAND "${EXE}" -l "${INPUT}"
  OUTPUT_VARIABLE count_out
  ERROR_VARIABLE count_err
  RESULT_VARIABLE count_rc)
string(STRIP "${count_out}" count_out)
if(NOT count_rc EQUAL 0)
  message(FATAL_ERROR "-l exited ${count_rc}, expected 0 (stderr: ${count_err})")
endif()
if(NOT count_out MATCHES "^ *2 ")
  message(FATAL_ERROR "-l on ${INPUT} printed '${count_out}', expected a count of 2")
endif()

execute_process(
  COMMAND "${EXE}" does-not-exist.txt
  OUTPUT_VARIABLE missing_out
  ERROR_VARIABLE missing_err
  RESULT_VARIABLE missing_rc)
if(NOT missing_rc EQUAL 1)
  message(FATAL_ERROR "unreadable file exited ${missing_rc}, expected 1")
endif()
if(NOT missing_err MATCHES "cannot open")
  message(FATAL_ERROR "unreadable file printed no diagnostic (stderr: '${missing_err}')")
endif()

message(STATUS "cli checks passed")
