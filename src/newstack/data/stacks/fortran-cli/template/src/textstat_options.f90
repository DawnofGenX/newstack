module textstat_options
  !! Argument parsing. Returns a status instead of printing, so a test can ask
  !! what the parser thought without redirecting stdout.
  implicit none
  private
  public :: options_t, parse_options, status_ok, status_help, status_version, status_usage

  integer, parameter :: status_ok = 0
  integer, parameter :: status_help = 1
  integer, parameter :: status_version = 2
  integer, parameter :: status_usage = 3

  integer, parameter :: kind_file = 1
  integer, parameter :: kind_terminator = 2
  integer, parameter :: kind_flag = 3

  type :: options_t
    integer :: status = status_ok
    character(len=:), allocatable :: message
    logical :: show_lines = .false.
    logical :: show_words = .false.
    logical :: show_bytes = .false.
    logical :: any_figure = .false.
    character(len=1024), allocatable :: files(:)
  end type options_t

contains

  function parse_options(args) result(opts)
    character(len=*), intent(in), dimension(:) :: args
    type(options_t) :: opts
    integer :: i, nfiles, index
    logical :: only

    ! Pass one: read the flags and count the operands.
    only = .false.
    nfiles = 0
    do i = 1, size(args)
      select case (argument_kind(args(i), only))
      case (kind_terminator)
        only = .true.
      case (kind_flag)
        call read_flag(args(i), opts)
        if (opts%status /= status_ok) return
      case default
        nfiles = nfiles + 1
      end select
    end do
    if (.not. opts%any_figure) then
      opts%show_lines = .true.
      opts%show_words = .true.
      opts%show_bytes = .true.
    end if

    ! Pass two: the same classification again, this time keeping the operands.
    allocate (opts%files(nfiles))
    if (nfiles > 0) then
      only = .false.
      index = 0
      do i = 1, size(args)
        select case (argument_kind(args(i), only))
        case (kind_terminator)
          only = .true.
        case (kind_flag)
          cycle
        case default
          index = index + 1
          opts%files(index) = trim(args(i))
        end select
      end do
    end if
  end function parse_options

  integer function argument_kind(arg, only) result(kind)
    character(len=*), intent(in) :: arg
    logical, intent(in) :: only
    if (only) then
      kind = kind_file
    else if (len_trim(arg) == 2 .and. arg(1:2) == '--') then
      kind = kind_terminator
    else if (len_trim(arg) > 1 .and. arg(1:1) == '-') then
      kind = kind_flag
    else
      kind = kind_file
    end if
  end function argument_kind

  subroutine read_flag(arg, opts)
    character(len=*), intent(in) :: arg
    type(options_t), intent(inout) :: opts
    integer :: i, n
    n = len_trim(arg)
    if (arg(1:2) == '--') then
      call read_long(trim(arg(3:n)), arg, opts)
      return
    end if
    do i = 2, n
      call read_short(arg(i:i), arg, opts)
      if (opts%status /= status_ok) return
    end do
  end subroutine read_flag

  subroutine read_long(name, arg, opts)
    character(len=*), intent(in) :: name
    character(len=*), intent(in) :: arg
    type(options_t), intent(inout) :: opts
    select case (name)
    case ('lines')
      opts%show_lines = .true.
      opts%any_figure = .true.
    case ('words')
      opts%show_words = .true.
      opts%any_figure = .true.
    case ('bytes')
      opts%show_bytes = .true.
      opts%any_figure = .true.
    case ('help')
      opts%status = status_help
    case ('version')
      opts%status = status_version
    case default
      call reject(opts, arg)
    end select
  end subroutine read_long

  subroutine read_short(letter, arg, opts)
    character(len=1), intent(in) :: letter
    character(len=*), intent(in) :: arg
    type(options_t), intent(inout) :: opts
    select case (letter)
    case ('l')
      opts%show_lines = .true.
      opts%any_figure = .true.
    case ('w')
      opts%show_words = .true.
      opts%any_figure = .true.
    case ('c')
      opts%show_bytes = .true.
      opts%any_figure = .true.
    case ('h')
      opts%status = status_help
    case ('V')
      opts%status = status_version
    case default
      call reject(opts, arg)
    end select
  end subroutine read_short

  subroutine reject(opts, arg)
    type(options_t), intent(inout) :: opts
    character(len=*), intent(in) :: arg
    opts%status = status_usage
    opts%message = 'unknown option: ' // trim(arg)
  end subroutine reject

end module textstat_options
