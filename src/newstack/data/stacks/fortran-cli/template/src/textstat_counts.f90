module textstat_counts
  !! Counting core: no IO, no arguments, no printing.
  use iso_fortran_env, only: int8, int64
  implicit none
  private
  public :: counts_t, counter_t, counts_add, is_space_byte

  type :: counts_t
    integer(int64) :: lines = 0_int64
    integer(int64) :: words = 0_int64
    integer(int64) :: bytes = 0_int64
  end type counts_t

  type :: counter_t
    type(counts_t) :: total = counts_t()
    logical :: in_word = .false.
  contains
    procedure :: reset => counter_reset
    procedure :: feed => counter_feed
    procedure :: value => counter_value
  end type counter_t

  integer(int8), parameter :: byte_lf = 10_int8

contains

  pure logical function is_space_byte(b) result(flag)
    integer(int8), intent(in) :: b
    integer :: value
    value = int(b)
    flag = value == 32 .or. value == 9 .or. value == 10 &
      .or. value == 13 .or. value == 11 .or. value == 12
  end function is_space_byte

  pure function counts_add(left, right) result(total)
    type(counts_t), intent(in) :: left
    type(counts_t), intent(in) :: right
    type(counts_t) :: total
    total%lines = left%lines + right%lines
    total%words = left%words + right%words
    total%bytes = left%bytes + right%bytes
  end function counts_add

  subroutine counter_reset(self)
    class(counter_t), intent(inout) :: self
    self%total = counts_t()
    self%in_word = .false.
  end subroutine counter_reset

  subroutine counter_feed(self, b)
    class(counter_t), intent(inout) :: self
    integer(int8), intent(in) :: b
    self%total%bytes = self%total%bytes + 1_int64
    if (b == byte_lf) self%total%lines = self%total%lines + 1_int64
    if (is_space_byte(b)) then
      self%in_word = .false.
    else if (.not. self%in_word) then
      self%in_word = .true.
      self%total%words = self%total%words + 1_int64
    end if
  end subroutine counter_feed

  pure function counter_value(self) result(c)
    class(counter_t), intent(in) :: self
    type(counts_t) :: c
    c = self%total
  end function counter_value

end module textstat_counts
