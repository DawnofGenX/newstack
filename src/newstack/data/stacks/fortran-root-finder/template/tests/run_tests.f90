module fortran_harness
  implicit none
  integer :: passed = 0, failed = 0
contains
  subroutine check(name, condition, detail)
    character(len=*), intent(in) :: name, detail
    logical, intent(in) :: condition
    if (condition) then
      passed = passed + 1
    else
      failed = failed + 1
      write (*, '(A)') 'FAIL ' // name
      if (len_trim(detail) > 0) write (*, '(A)') '     ' // trim(detail)
    end if
  end subroutine check
end module fortran_harness

module test_functions
  implicit none
contains
  pure function square_minus_two(x) result(y)
    real(8), intent(in) :: x
    real(8) :: y
    y = x*x - 2.0d0
  end function square_minus_two
end module test_functions

program run_tests
  use iso_fortran_env, only: output_unit, error_unit
  use fortran_harness
  use root_find, only: bisect, bracket_error
  use root_options, only: options_t, parse_options, status_ok, status_help, status_usage
  use root_runner, only: run, demo_function
  use test_functions, only: square_minus_two
  implicit none
  type(options_t) :: opts
  type(bracket_error) :: err
  real(8) :: root
  integer :: iterations, code, unit, err_unit, ios
  character(len=256) :: line

  call bisect(square_minus_two, 1.0d0, 2.0d0, 1.0d-12, 200, root, iterations, err)
  call check('sqrt 2 root', abs(root - 1.4142135623730951d0) < 1.0d-9, '')
  call check('sqrt 2 iterations', iterations > 0 .and. iterations <= 200, '')

  call bisect(square_minus_two, -2.0d0, -1.0d0, 1.0d-12, 200, root, iterations, err)
  call check('negative root', abs(root + 1.4142135623730951d0) < 1.0d-9, '')

  call bisect(square_minus_two, 2.0d0, 3.0d0, 1.0d-12, 200, root, iterations, err)
  call check('unbracketed interval is refused', index(err%message, 'do not bracket') > 0, err%message)

  call bisect(square_minus_two, 1.0d0, 2.0d0, 0.0d0, 200, root, iterations, err)
  call check('zero tolerance is refused', index(err%message, 'tolerance') > 0, err%message)

  call bisect(square_minus_two, 1.0d0, 2.0d0, 1.0d-12, 0, root, iterations, err)
  call check('zero budget is refused', index(err%message, 'budget') > 0, err%message)

  call bisect(square_minus_two, -1.0d0, 2.0d0, 1.0d-2, 2, root, iterations, err)
  call check('exhausted budget is reported', index(err%message, 'exhausted') > 0, err%message)

  opts = parse_options_noargs()
  call check('empty args are a usage error', opts%status == status_usage, opts%message)
  opts = parse_options_help()
  call check('--help is help', opts%status == status_help, opts%message)

  open (newunit=unit, file='build/out.txt', status='replace', action='readwrite')
  open (newunit=err_unit, file='build/err.txt', status='replace', action='readwrite')
  code = run([character(len=32) :: '2', '3'], unit, err_unit)
  rewind (unit)
  read (unit, '(A)', iostat=ios) line
  call check('demo root exits zero', code == 0, '')
  call check('demo root is near 2.09455', index(line, 'root=2.0945') == 1, line)

  close (unit, status='delete')
  close (err_unit, status='delete')

  write (*, '(A,I0,A,I0,A,I0)') 'checks: ', passed + failed, ', passed: ', passed, ', failed: ', failed
  if (failed > 0) call exit(1)
  call exit(0)
contains
  function parse_options_noargs() result(o)
    type(options_t) :: o
    character(len=8), dimension(0) :: none
    call parse_options(none, o)
  end function parse_options_noargs
  function parse_options_help() result(o)
    type(options_t) :: o
    call parse_options([character(len=8) :: '--help'], o)
  end function parse_options_help
end program run_tests
