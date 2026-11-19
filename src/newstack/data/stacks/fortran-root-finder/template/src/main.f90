program main
  use iso_fortran_env, only: output_unit, error_unit
  use root_runner, only: run
  implicit none
  character(len=128), allocatable :: args(:)
  integer :: n, i
  n = command_argument_count()
  allocate (args(max(1, n)))
  do i = 1, n
    call get_command_argument(i, args(i))
  end do
  if (n == 0) then
    call get_command_argument(0, args(1))
    args = [args(1)]
    n = 1
  end if
  call exit(run(args(1:n), output_unit, error_unit))
end program main
