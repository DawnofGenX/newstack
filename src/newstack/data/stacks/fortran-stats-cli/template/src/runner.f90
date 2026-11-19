module runner
  use iso_fortran_env, only: input_unit, output_unit, error_unit
  use stats, only: stats_mean, stats_median, stats_stdev
  implicit none
contains

  integer function run(args, out, err) result(code)
    character(len=*), intent(in) :: args(:)
    integer, intent(in) :: out, err
    real, allocatable :: values(:)
    real :: v
    integer :: n, capacity, i, ios
    character(len=256) :: msg

    ! handle options
    if (size(args) > 0) then
      if (trim(args(1)) == '--help' .or. trim(args(1)) == '-h') then
        write (out, '(A)') 'Usage: stats [options]'
        write (out, '(A)') 'Read numbers from stdin and print mean, median, stdev.'
        code = 0
        return
      end if
      if (trim(args(1)) == '--version' .or. trim(args(1)) == '-V') then
        write (out, '(A)') '0.1.0'
        code = 0
        return
      end if
      if (args(1)(1:1) == '-') then
        write (err, '(A)') 'unknown option: ' // trim(args(1))
        code = 2
        return
      end if
    end if

    ! read numbers from stdin
    capacity = 1024
    allocate (values(capacity))
    n = 0
    do
      read (input_unit, *, iostat=ios) v
      if (ios /= 0) exit
      n = n + 1
      if (n > capacity) then
        ! grow
        block
          real, allocatable :: tmp(:)
          allocate (tmp(capacity*2))
          tmp(1:capacity) = values(1:capacity)
          call move_alloc(tmp, values)
          capacity = capacity * 2
        end block
      end if
      values(n) = v
    end do

    if (n == 0) then
      write (err, '(A)') 'no numbers on stdin'
      code = 1
      return
    end if

    write (out, '(A,F12.6)') 'mean:   ', stats_mean(values, n)
    write (out, '(A,F12.6)') 'median: ', stats_median(values, n)
    write (out, '(A,F12.6)') 'stdev:  ', stats_stdev(values, n)
    code = 0
  end function run

end module runner