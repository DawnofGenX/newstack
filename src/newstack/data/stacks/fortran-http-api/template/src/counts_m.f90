module counts_m
  ! wc semantics over raw bytes: a line is 0x0A, a word is a run of bytes that is
  ! not one of the six ASCII separators, and the size is the number of bytes.
  use, intrinsic :: iso_c_binding, only: c_int8_t
  implicit none
  private
  public :: count_bytes

contains

  function is_sep(value) result(sep)
    integer, intent(in) :: value
    logical :: sep
    sep = value == 32 .or. value == 9 .or. value == 10 .or. value == 13 &
          .or. value == 11 .or. value == 12
  end function is_sep

  subroutine count_bytes(buf, n, lines, words, nbytes)
    integer(c_int8_t), intent(in) :: buf(:)
    integer, intent(in) :: n
    integer, intent(out) :: lines, words, nbytes
    integer :: i, value
    logical :: in_word

    lines = 0
    words = 0
    nbytes = n
    in_word = .false.
    do i = 1, n
      value = iand(int(buf(i)), 255)
      if (value == 10) lines = lines + 1
      if (is_sep(value)) then
        in_word = .false.
      else if (.not. in_word) then
        words = words + 1
        in_word = .true.
      end if
    end do
  end subroutine count_bytes

end module counts_m
