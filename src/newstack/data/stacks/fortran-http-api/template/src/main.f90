program textstat
  ! Entry point: --selftest runs the in-process checks, otherwise the process
  ! becomes the server. HOST and PORT come from the environment, and a bad PORT is
  ! a usage error (exit 2) rather than a crash.
  use, intrinsic :: iso_c_binding, only: c_int
  use server_m, only: serve
  use selftest_m, only: run_selftest
  implicit none

  character(len=256) :: arg, value
  integer :: i, argc, status, port, code, ios
  logical :: selftest, have_port

  selftest = .false.
  argc = command_argument_count()
  do i = 1, argc
    call get_command_argument(i, arg)
    if (trim(arg) == '--selftest') selftest = .true.
  end do

  if (selftest) then
    code = run_selftest()
    call exit(code)
  end if

  have_port = .false.
  port = 8080
  value = ''
  call get_environment_variable('PORT', value, status=status)
  if (status == 0 .and. len_trim(value) > 0) then
    read (value, *, iostat=ios) port
    if (ios /= 0 .or. port <= 0 .or. port > 65535) then
      write (0, '(A, A)') 'PORT is not a port: ', trim(value)
      call exit(2)
    end if
    have_port = .true.
  end if

  if (.not. have_port) port = 8080
  call serve(port)
end program textstat
