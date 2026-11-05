module json_m
  ! A small recursive-descent JSON reader that only needs one member: "text".
  ! Anything else is skipped structurally, so a nested object does not confuse the
  ! scan, and a document with trailing garbage is rejected instead of half-read.
  use, intrinsic :: iso_c_binding, only: c_int8_t
  use bytes_m, only: bytes, bytes_init, bytes_put
  implicit none
  private

  public :: json_read, KEY_TEXT, KEY_MISSING, KEY_INVALID
  integer, parameter :: KEY_TEXT = 0, KEY_MISSING = 1, KEY_INVALID = 2

  integer(c_int8_t), allocatable, save :: src(:)
  integer, save :: pos = 1
  integer, save :: src_len = 0

contains

  function value_at(index) result(value)
    integer, intent(in) :: index
    integer :: value
    value = iand(int(src(index)), 255)
  end function value_at

  function is_ws(value) result(flag)
    integer, intent(in) :: value
    logical :: flag
    flag = value == 32 .or. value == 9 .or. value == 10 .or. value == 13
  end function is_ws

  subroutine skip_ws()
    do while (pos <= src_len)
      if (.not. is_ws(value_at(pos))) return
      pos = pos + 1
    end do
  end subroutine skip_ws

  function hex_value(value) result(digit)
    integer, intent(in) :: value
    integer :: digit
    digit = -1
    if (value >= 48 .and. value <= 57) digit = value - 48
    if (value >= 97 .and. value <= 102) digit = value - 97 + 10
    if (value >= 65 .and. value <= 70) digit = value - 65 + 10
  end function hex_value

  subroutine read_hex4(code, ok)
    integer, intent(out) :: code
    logical, intent(inout) :: ok
    integer :: i, digit
    code = 0
    if (pos + 3 > src_len) then
      ok = .false.
      return
    end if
    do i = 1, 4
      digit = hex_value(value_at(pos))
      if (digit < 0) then
        ok = .false.
        return
      end if
      code = code * 16 + digit
      pos = pos + 1
    end do
  end subroutine read_hex4

  subroutine put_code_point(out, code)
    type(bytes), intent(inout) :: out
    integer, intent(in) :: code
    if (code < 128) then
      call bytes_put(out, code)
    else if (code < 2048) then
      call bytes_put(out, 192 + code / 64)
      call bytes_put(out, 128 + mod(code, 64))
    else if (code < 65536) then
      call bytes_put(out, 224 + code / 4096)
      call bytes_put(out, 128 + mod(code / 64, 64))
      call bytes_put(out, 128 + mod(code, 64))
    else
      call bytes_put(out, 240 + code / 262144)
      call bytes_put(out, 128 + mod(code / 4096, 64))
      call bytes_put(out, 128 + mod(code / 64, 64))
      call bytes_put(out, 128 + mod(code, 64))
    end if
  end subroutine put_code_point

  subroutine parse_string(out, ok)
    ! Called with pos on the opening quote; leaves pos after the closing quote.
    type(bytes), intent(inout) :: out
    logical, intent(inout) :: ok
    integer :: value, escape, code, low

    if (pos > src_len) then
      ok = .false.
      return
    end if
    if (value_at(pos) /= 34) then
      ok = .false.
      return
    end if
    pos = pos + 1
    do
      if (pos > src_len) then
        ok = .false.
        return
      end if
      value = value_at(pos)
      if (value == 34) then
        pos = pos + 1
        return
      end if
      if (value < 32) then
        ok = .false.
        return
      end if
      if (value /= 92) then
        call bytes_put(out, value)
        pos = pos + 1
      else
        pos = pos + 1
        if (pos > src_len) then
          ok = .false.
          return
        end if
        escape = value_at(pos)
        pos = pos + 1
        select case (escape)
        case (34)
          call bytes_put(out, 34)
        case (92)
          call bytes_put(out, 92)
        case (47)
          call bytes_put(out, 47)
        case (98)
          call bytes_put(out, 8)
        case (102)
          call bytes_put(out, 12)
        case (110)
          call bytes_put(out, 10)
        case (114)
          call bytes_put(out, 13)
        case (116)
          call bytes_put(out, 9)
        case (117)
          call read_hex4(code, ok)
          if (.not. ok) return
          if (code >= 55296 .and. code <= 56319) then
            ! a high surrogate needs the low half or it is not a code point
            if (pos + 1 > src_len) then
              ok = .false.
              return
            end if
            if (value_at(pos) /= 92 .or. value_at(pos + 1) /= 117) then
              ok = .false.
              return
            end if
            pos = pos + 2
            call read_hex4(low, ok)
            if (.not. ok) return
            if (low < 56320 .or. low > 57343) then
              ok = .false.
              return
            end if
            code = 65536 + (code - 55296) * 1024 + (low - 56320)
          end if
          call put_code_point(out, code)
        case default
          ok = .false.
          return
        end select
      end if
    end do
  end subroutine parse_string

  recursive subroutine skip_value(depth, ok)
    integer, intent(in) :: depth
    logical, intent(inout) :: ok
    type(bytes) :: scratch
    integer :: value

    if (depth > 32) then
      ok = .false.
      return
    end if
    call skip_ws()
    if (pos > src_len) then
      ok = .false.
      return
    end if
    value = value_at(pos)
    select case (value)
    case (34)
      call bytes_init(scratch, 16)
      call parse_string(scratch, ok)
    case (123) ! {
      pos = pos + 1
      call skip_ws()
      if (pos <= src_len .and. value_at(pos) == 125) then
        pos = pos + 1
        return
      end if
      do
        call skip_ws()
        call bytes_init(scratch, 16)
        call parse_string(scratch, ok)
        if (.not. ok) return
        call skip_ws()
        if (pos > src_len .or. value_at(pos) /= 58) then
          ok = .false.
          return
        end if
        pos = pos + 1
        call skip_value(depth + 1, ok)
        if (.not. ok) return
        call skip_ws()
        if (pos > src_len) then
          ok = .false.
          return
        end if
        value = value_at(pos)
        pos = pos + 1
        if (value == 125) return
        if (value /= 44) then
          ok = .false.
          return
        end if
      end do
    case (91) ! [
      pos = pos + 1
      call skip_ws()
      if (pos <= src_len .and. value_at(pos) == 93) then
        pos = pos + 1
        return
      end if
      do
        call skip_value(depth + 1, ok)
        if (.not. ok) return
        call skip_ws()
        if (pos > src_len) then
          ok = .false.
          return
        end if
        value = value_at(pos)
        pos = pos + 1
        if (value == 93) return
        if (value /= 44) then
          ok = .false.
          return
        end if
      end do
    case (116) ! true
      call expect_word("true", ok)
    case (102) ! false
      call expect_word("false", ok)
    case (110) ! null
      call expect_word("null", ok)
    case default ! number
      call skip_number(ok)
    end select
  end subroutine skip_value

  subroutine expect_word(word, ok)
    character(len=*), intent(in) :: word
    logical, intent(inout) :: ok
    integer :: i
    do i = 1, len(word)
      if (pos > src_len) then
        ok = .false.
        return
      end if
      if (value_at(pos) /= iachar(word(i:i))) then
        ok = .false.
        return
      end if
      pos = pos + 1
    end do
  end subroutine expect_word

  subroutine skip_number(ok)
    logical, intent(inout) :: ok
    integer :: value, digits
    digits = 0
    do while (pos <= src_len)
      value = value_at(pos)
      if (value == 45 .or. value == 43 .or. value == 46 .or. value == 101 .or. value == 69) then
        pos = pos + 1
      else if (value >= 48 .and. value <= 57) then
        digits = digits + 1
        pos = pos + 1
      else
        exit
      end if
    end do
    if (digits == 0) ok = .false.
  end subroutine skip_number

  function same_as_text(key) result(match)
    type(bytes), intent(in) :: key
    logical :: match
    integer, parameter :: wanted(4) = [116, 101, 120, 116]
    integer :: i
    match = .false.
    if (key%n /= 4) return
    do i = 1, 4
      if (iand(int(key%data(i)), 255) /= wanted(i)) return
    end do
    match = .true.
  end function same_as_text

  subroutine json_read(buf, n, kind, text)
    integer(c_int8_t), intent(in) :: buf(:)
    integer, intent(in) :: n
    integer, intent(out) :: kind
    type(bytes), intent(out) :: text

    type(bytes) :: key, value
    logical :: ok, found
    integer :: current

    call bytes_init(text, 64)
    kind = KEY_INVALID
    if (n <= 0) return
    if (allocated(src)) deallocate (src)
    allocate (src(n))
    src(1:n) = buf(1:n)
    src_len = n
    pos = 1
    ok = .true.
    found = .false.

    call skip_ws()
    if (pos > src_len) return
    if (value_at(pos) /= 123) return
    pos = pos + 1

    do
      call skip_ws()
      if (pos > src_len) return
      if (value_at(pos) == 125) then
        pos = pos + 1
        exit
      end if
      call bytes_init(key, 8)
      call parse_string(key, ok)
      if (.not. ok) return
      call skip_ws()
      if (pos > src_len) return
      if (value_at(pos) /= 58) return
      pos = pos + 1
      call skip_ws()
      if (pos > src_len) return

      if (same_as_text(key)) then
        if (value_at(pos) == 34) then
          call bytes_init(value, 64)
          call parse_string(value, ok)
          if (.not. ok) return
          text = value
          found = .true.
        else
          call skip_value(0, ok)
          if (.not. ok) return
          found = .false.
        end if
      else
        call skip_value(0, ok)
        if (.not. ok) return
      end if

      call skip_ws()
      if (pos > src_len) return
      current = value_at(pos)
      pos = pos + 1
      if (current == 125) exit
      if (current /= 44) return
    end do

    call skip_ws()
    if (pos <= src_len) return
    if (found) then
      kind = KEY_TEXT
    else
      kind = KEY_MISSING
    end if
  end subroutine json_read

end module json_m
