module root_runner
  use root_find, only: bisect, bracket_error
  use root_options, only: options_t, parse_options, status_ok, status_help, status_usage, &
    program_name
  implicit none
  private
  public :: run, demo_function
contains
  pure function demo_function(x) result(y)
    real(8), intent(in) :: x
    real(8) :: y
    y = x*x*x - 2.0d0*x - 5.0d0
  end function demo_function

  integer function run(args, out, err_unit) result(code)
    character(len=*), intent(in) :: args(:)
    integer, intent(in) :: out, err_unit
    type(options_t) :: opts
    type(bracket_error) :: err
    real(8) :: root
    integer :: iterations
    character(len=128) :: line
    call parse_options(args, opts)
    select case (opts%status)
    case (status_help)
      write (out, '(A)') 'Find a real root of x^3 - 2x - 5 by bisection.'
      write (out, '(A)') 'Usage: ' // program_name // ' [--tol N] [--iter N] LO HI'
      code = 0
      return
    case (status_usage)
      write (err_unit, '(A)') trim(program_name) // ': ' // trim(opts%message)
      write (err_unit, '(A)') "Try '" // trim(program_name) // " --help' for more information."
      code = 2
      return
    end select
    call bisect(demo_function, opts%lo, opts%hi, opts%tol, opts%max_iter, root, iterations, err)
    if (len_trim(err%message) > 0) then
      write (err_unit, '(A)') trim(program_name) // ': ' // trim(err%message)
      code = 1
      return
    end if
    write (line, '(A,F0.10,A,I0,A)') 'root=', root, ' iterations=', iterations, ''
    write (out, '(A)') trim(line)
    code = 0
  end function run
end module root_runner
