program main
  use iso_fortran_env, only: output_unit, error_unit
  use runner, only: run
  implicit none
  integer :: count, i, code
  character(len=4096) :: buffer
  character(len=4096), allocatable :: args(:)

  count = command_argument_count()
  allocate (args(count))
  do i = 1, count
    buffer = ''
    call get_command_argument(i, buffer)
    args(i) = trim(buffer)
  end do
  code = run(args, output_unit, error_unit)
  call exit(code)
end program main