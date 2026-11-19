module root_options
  implicit none
  private
  public :: options_t, parse_options, status_ok, status_help, status_usage, program_name
  integer, parameter :: status_ok = 0, status_help = 1, status_usage = 2
  character(len=*), parameter :: program_name = "{{ npm_name }}"
  type :: options_t
    real(8) :: lo = 0.0d0, hi = 0.0d0
    real(8) :: tol = 1.0d-9
    integer :: max_iter = 200
    integer :: status = status_ok
    character(len=160) :: message = ''
  end type options_t
contains
  subroutine parse_options(args, opts)
    character(len=*), intent(in) :: args(:)
    type(options_t), intent(out) :: opts
    integer :: i, ios, seen
    character(len=64) :: word
    seen = 0
    i = 1
    do while (i <= size(args))
      word = trim(args(i))
      select case (word)
      case ('-h', '--help')
        opts%status = status_help
        return
      case ('--tol')
        if (i >= size(args)) then
          opts%status = status_usage
          opts%message = '--tol needs a value'
          return
        end if
        read (args(i+1), *, iostat=ios) opts%tol
        if (ios /= 0 .or. opts%tol <= 0.0d0) then
          opts%status = status_usage
          opts%message = '--tol must be a positive number'
          return
        end if
        i = i + 2
      case ('--iter')
        if (i >= size(args)) then
          opts%status = status_usage
          opts%message = '--iter needs a value'
          return
        end if
        read (args(i+1), *, iostat=ios) opts%max_iter
        if (ios /= 0 .or. opts%max_iter < 1) then
          opts%status = status_usage
          opts%message = '--iter must be a positive integer'
          return
        end if
        i = i + 2
      case default
        if (seen >= 2 .or. word(1:1) == '-') then
          opts%status = status_usage
          opts%message = 'unexpected argument: ' // word
          return
        end if
        read (word, *, iostat=ios) opts%lo
        if (ios /= 0) then
          opts%status = status_usage
          opts%message = 'endpoints must be numbers'
          return
        end if
        seen = 1
        i = i + 1
        if (i <= size(args)) then
          read (args(i), *, iostat=ios) opts%hi
          if (ios /= 0) then
            opts%status = status_usage
            opts%message = 'endpoints must be numbers'
            return
          end if
          seen = 2
          i = i + 1
        end if
      end select
    end do
    if (seen /= 2) then
      opts%status = status_usage
      opts%message = 'expected two endpoints'
    end if
  end subroutine parse_options
end module root_options
