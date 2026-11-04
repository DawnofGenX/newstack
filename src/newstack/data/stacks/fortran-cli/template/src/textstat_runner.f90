module textstat_runner
  !! Everything that touches the process: argv, files, stdout, stderr, exit code.
  use iso_fortran_env, only: int8, int64
  use textstat_counts, only: counts_t, counter_t, counts_add
  use textstat_options, only: options_t, parse_options, status_help, status_version, &
    status_usage
  implicit none
  private
  public :: run, program_name

  character(len=*), parameter :: program_name = '{{ npm_name }}'
  character(len=*), parameter :: version = '0.1.0'

contains

  integer function run(args, out, err) result(code)
    character(len=*), intent(in), dimension(:) :: args
    integer, intent(in) :: out
    integer, intent(in) :: err
    type(options_t) :: opts
    type(counts_t), allocatable :: rows(:)
    character(len=1024), allocatable :: labels(:)
    type(counts_t) :: total
    integer :: i, nrows, width
    logical :: ok, any_ok

    opts = parse_options(args)
    select case (opts%status)
    case (status_help)
      write (out, '(A)') usage_lines()
      code = 0
      return
    case (status_version)
      write (out, '(A)') version
      code = 0
      return
    case (status_usage)
      write (err, '(A)') program_name // ': ' // opts%message
      write (err, '(A)') "Try '" // program_name // " --help' for more information."
      code = 2
      return
    end select

    if (size(opts%files) == 0) then
      allocate (labels(1))
      labels(1) = '-'
    else
      allocate (labels(size(opts%files)))
      labels = opts%files
    end if

    allocate (rows(size(labels)))
    nrows = 0
    total = counts_t()
    any_ok = .false.
    do i = 1, size(labels)
      call count_operand(trim(labels(i)), rows(nrows + 1), err, ok)
      if (ok) then
        nrows = nrows + 1
        total = counts_add(total, rows(nrows))
        any_ok = .true.
      end if
    end do

    width = row_width(rows, nrows, opts, size(labels) > 1, total)
    do i = 1, nrows
      write (out, '(A)') row_text(rows(i), opts, width) // ' ' // trim(labels(i))
    end do
    if (size(labels) > 1) then
      write (out, '(A)') row_text(total, opts, width) // ' total'
    end if

    code = 0
    if (.not. any_ok) then
      code = 1
    else if (nrows < size(labels)) then
      code = 1
    end if
  end function run

  subroutine count_operand(path, c, err, ok)
    character(len=*), intent(in) :: path
    type(counts_t), intent(out) :: c
    integer, intent(in) :: err
    logical, intent(out) :: ok
    type(counter_t) :: counter
    integer :: unit, ios
    integer(int8) :: b

    ok = .false.
    call counter%reset()
    if (trim(path) == '-') then
      open (newunit=unit, file='/dev/stdin', access='stream', form='unformatted', &
        action='read', status='old', iostat=ios)
    else
      open (newunit=unit, file=trim(path), access='stream', form='unformatted', &
        action='read', status='old', iostat=ios)
    end if
    if (ios /= 0) then
      write (err, '(A)') "error: cannot open '" // trim(path) // "'"
      c = counts_t()
      return
    end if
    do
      read (unit, iostat=ios) b
      if (ios /= 0) exit
      call counter%feed(b)
    end do
    close (unit)
    c = counter%value()
    ok = .true.
  end subroutine count_operand

  integer function row_width(rows, nrows, opts, with_total, total) result(width)
    type(counts_t), intent(in) :: rows(:)
    integer, intent(in) :: nrows
    type(options_t), intent(in) :: opts
    logical, intent(in) :: with_total
    type(counts_t), intent(in) :: total
    integer :: i
    width = 1
    do i = 1, nrows
      width = max(width, widest(rows(i), opts))
    end do
    if (with_total) width = max(width, widest(total, opts))
  end function row_width

  integer function widest(c, opts) result(width)
    type(counts_t), intent(in) :: c
    type(options_t), intent(in) :: opts
    width = 1
    if (opts%show_lines) width = max(width, figure_digits(c%lines))
    if (opts%show_words) width = max(width, figure_digits(c%words))
    if (opts%show_bytes) width = max(width, figure_digits(c%bytes))
  end function widest

  integer function figure_digits(value) result(n)
    integer(int64), intent(in) :: value
    character(len=32) :: buffer
    write (buffer, '(I0)') value
    n = len_trim(buffer)
  end function figure_digits

  function row_text(c, opts, width) result(text)
    type(counts_t), intent(in) :: c
    type(options_t), intent(in) :: opts
    integer, intent(in) :: width
    character(len=:), allocatable :: text
    text = ''
    if (opts%show_lines) text = text // cell(c%lines, width) // ' '
    if (opts%show_words) text = text // cell(c%words, width) // ' '
    if (opts%show_bytes) text = text // cell(c%bytes, width) // ' '
    text = text(1:len(text) - 1)
  end function row_text

  function cell(value, width) result(text)
    integer(int64), intent(in) :: value
    integer, intent(in) :: width
    character(len=:), allocatable :: text
    character(len=32) :: buffer
    integer :: used
    write (buffer, '(I0)') value
    used = len_trim(buffer)
    text = repeat(' ', max(0, width - used)) // trim(buffer)
  end function cell

  function usage_lines() result(text)
    character(len=:), allocatable :: text
    text = 'Count lines, words and bytes in text files.' // new_line('a') &
      // new_line('a') &
      // 'Usage: ' // program_name // ' [OPTION]... [FILE]...' // new_line('a') &
      // 'With no FILE, or when FILE is -, read standard input.' // new_line('a') &
      // new_line('a') &
      // '  -l, --lines    print the newline count' // new_line('a') &
      // '  -w, --words    print the word count' // new_line('a') &
      // '  -c, --bytes    print the byte count' // new_line('a') &
      // '  -h, --help     show this help and exit' // new_line('a') &
      // '  -V, --version  show the version and exit'
  end function usage_lines

end module textstat_runner
