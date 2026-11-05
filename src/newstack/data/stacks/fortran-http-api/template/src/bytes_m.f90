module bytes_m
  ! A byte buffer. Fortran strings are fine for ASCII, but the wire carries UTF-8
  ! and JSON escapes are byte-level, so everything that touches a body is an
  ! int8 array and only the head is ever turned back into a character string.
  use, intrinsic :: iso_c_binding, only: c_int8_t
  implicit none
  private

  type :: bytes
     integer(c_int8_t), allocatable :: data(:)
     integer :: n = 0
  end type bytes

  public :: bytes, bytes_init, bytes_put, bytes_put_str, bytes_put_int, bytes_as_string

contains

  subroutine bytes_init(b, capacity)
    type(bytes), intent(out) :: b
    integer, intent(in), optional :: capacity
    integer :: size_
    size_ = 256
    if (present(capacity)) size_ = capacity
    allocate(b%data(size_))
    b%n = 0
  end subroutine bytes_init

  subroutine ensure(b, extra)
    type(bytes), intent(inout) :: b
    integer, intent(in) :: extra
    integer(c_int8_t), allocatable :: bigger(:)
    if (b%n + extra <= size(b%data)) return
    allocate(bigger(max(2 * size(b%data), b%n + extra)))
    if (b%n > 0) bigger(1:b%n) = b%data(1:b%n)
    call move_alloc(bigger, b%data)
  end subroutine ensure

  subroutine bytes_put(b, value)
    type(bytes), intent(inout) :: b
    integer, intent(in) :: value
    call ensure(b, 1)
    b%n = b%n + 1
    b%data(b%n) = int(value, c_int8_t)
  end subroutine bytes_put

  subroutine bytes_put_str(b, text)
    type(bytes), intent(inout) :: b
    character(len=*), intent(in) :: text
    integer :: i
    do i = 1, len(text)
      call bytes_put(b, iachar(text(i:i)))
    end do
  end subroutine bytes_put_str

  subroutine bytes_put_int(b, value)
    type(bytes), intent(inout) :: b
    integer, intent(in) :: value
    character(len=24) :: digits
    write (digits, '(I0)') value
    call bytes_put_str(b, trim(digits))
  end subroutine bytes_put_int

  function bytes_as_string(b) result(text)
    type(bytes), intent(in) :: b
    character(len=:), allocatable :: text
    character(len=b%n) :: tmp
    integer :: i
    do i = 1, b%n
      tmp(i:i) = achar(iand(int(b%data(i)), 255))
    end do
    text = tmp
  end function bytes_as_string

end module bytes_m
