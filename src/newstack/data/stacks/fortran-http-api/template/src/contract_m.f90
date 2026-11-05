module contract_m
  ! The route table as one pure subroutine: method, target and body in, a status
  ! and a JSON document out. Nothing here opens a socket, so the whole contract is
  ! testable in a loop inside the test program.
  use, intrinsic :: iso_c_binding, only: c_int8_t
  use bytes_m, only: bytes, bytes_init, bytes_put, bytes_put_str, bytes_put_int
  use counts_m, only: count_bytes
  use json_m, only: json_read, KEY_TEXT, KEY_MISSING, KEY_INVALID
  implicit none
  private

  public :: route, json_escape, percent_decode

contains

  subroutine put_ascii(out, text)
    type(bytes), intent(inout) :: out
    character(len=*), intent(in) :: text
    call bytes_put_str(out, text)
  end subroutine put_ascii

  subroutine json_escape(raw, n, out)
    integer(c_int8_t), intent(in) :: raw(:)
    integer, intent(in) :: n
    type(bytes), intent(inout) :: out
    integer :: i, value
    character(len=6) :: hex
    do i = 1, n
      value = iand(int(raw(i)), 255)
      select case (value)
      case (34)
        call put_ascii(out, char(92) // '"')
      case (92)
        call put_ascii(out, char(92) // char(92))
      case (10)
        call put_ascii(out, char(92) // 'n')
      case (13)
        call put_ascii(out, char(92) // 'r')
      case (9)
        call put_ascii(out, char(92) // 't')
      case (8)
        call put_ascii(out, char(92) // 'b')
      case (12)
        call put_ascii(out, char(92) // 'f')
      case default
        if (value < 32) then
          write (hex, '(A, Z4.4)') char(92) // 'u', value
          call put_ascii(out, hex)
        else
          call bytes_put(out, value)
        end if
      end select
    end do
  end subroutine json_escape

  function hex_digit(value) result(digit)
    integer, intent(in) :: value
    integer :: digit
    digit = -1
    if (value >= 48 .and. value <= 57) digit = value - 48
    if (value >= 97 .and. value <= 102) digit = value - 97 + 10
    if (value >= 65 .and. value <= 70) digit = value - 65 + 10
  end function hex_digit

  subroutine percent_decode(source, out)
    ! '+' is a space and %XX is a byte (never a character), matching
    ! java.net.URLDecoder and the rest of the family.
    character(len=*), intent(in) :: source
    type(bytes), intent(out) :: out
    integer :: i, value, hi, lo
    call bytes_init(out, len(source) + 1)
    i = 1
    do while (i <= len(source))
      value = iachar(source(i:i))
      if (value == 43) then
        call bytes_put(out, 32)
        i = i + 1
      else if (value == 37 .and. i + 2 <= len(source)) then
        hi = hex_digit(iachar(source(i + 1:i + 1)))
        lo = hex_digit(iachar(source(i + 2:i + 2)))
        if (hi >= 0 .and. lo >= 0) then
          call bytes_put(out, hi * 16 + lo)
          i = i + 3
        else
          call bytes_put(out, value)
          i = i + 1
        end if
      else
        call bytes_put(out, value)
        i = i + 1
      end if
    end do
  end subroutine percent_decode

  subroutine stats_document(text, n, out)
    integer(c_int8_t), intent(in) :: text(:)
    integer, intent(in) :: n
    type(bytes), intent(out) :: out
    integer :: lines, words, nbytes
    call count_bytes(text, n, lines, words, nbytes)
    call bytes_init(out, n + 64)
    call put_ascii(out, '{"text":"')
    call json_escape(text, n, out)
    call put_ascii(out, '","lines":')
    call bytes_put_int(out, lines)
    call put_ascii(out, ',"words":')
    call bytes_put_int(out, words)
    call put_ascii(out, ',"bytes":')
    call bytes_put_int(out, nbytes)
    call bytes_put(out, 125)
  end subroutine stats_document

  subroutine error_document(code, out)
    character(len=*), intent(in) :: code
    type(bytes), intent(out) :: out
    call bytes_init(out, 32)
    call put_ascii(out, '{"error":"')
    call put_ascii(out, code)
    call put_ascii(out, '"}')
  end subroutine error_document

  function path_of(target) result(path)
    character(len=*), intent(in) :: target
    character(len=:), allocatable :: path
    integer :: mark
    mark = index(target, '?')
    if (mark == 0) then
      path = target
    else
      path = target(1:mark - 1)
    end if
  end function path_of

  subroutine query_text(target, text, found)
    character(len=*), intent(in) :: target
    type(bytes), intent(out) :: text
    logical, intent(out) :: found
    character(len=:), allocatable :: query, piece, key, value
    integer :: mark, start, amp, eq
    integer(c_int8_t), allocatable :: decoded(:)
    type(bytes) :: decoded_bytes

    call bytes_init(text, 16)
    found = .false.
    mark = index(target, '?')
    if (mark == 0) return
    query = target(mark + 1:)
    start = 1
    do while (start <= len(query))
      amp = index(query(start:), '&')
      if (amp == 0) then
        if (start <= len(query)) then
          piece = query(start:)
        else
          piece = ''
        end if
        start = len(query) + 1
      else
        piece = query(start:start + amp - 2)
        start = start + amp
      end if
      if (len(piece) > 0 .and. .not. found) then
        eq = index(piece, '=')
        if (eq == 0) then
          key = piece
          value = ''
        else
          key = piece(1:eq - 1)
          value = piece(eq + 1:)
        end if
        call percent_decode(key, decoded_bytes)
        if (decoded_bytes%n == 4) then
          if (iand(int(decoded_bytes%data(1)), 255) == 116 .and. &
              iand(int(decoded_bytes%data(2)), 255) == 101 .and. &
              iand(int(decoded_bytes%data(3)), 255) == 120 .and. &
              iand(int(decoded_bytes%data(4)), 255) == 116) then
            call percent_decode(value, text)
            found = .true.
          end if
        end if
        if (allocated(decoded)) deallocate (decoded)
      end if
    end do
  end subroutine query_text

  subroutine route(method, target, body, n, status, out)
    character(len=*), intent(in) :: method
    character(len=*), intent(in) :: target
    integer(c_int8_t), intent(in) :: body(:)
    integer, intent(in) :: n
    integer, intent(out) :: status
    type(bytes), intent(out) :: out

    character(len=:), allocatable :: path
    logical :: found
    type(bytes) :: text
    integer :: kind

    path = path_of(target)

    if (path == '/health') then
      if (method /= 'GET') then
        status = 405
        call error_document('method_not_allowed', out)
      else
        status = 200
        call bytes_init(out, 16)
        call put_ascii(out, '{"status":"ok"}')
      end if
      return
    end if

    if (path == '/stats') then
      if (method == 'GET') then
        call query_text(target, text, found)
        if (found) then
          status = 200
          call stats_document(text%data, text%n, out)
        else
          status = 422
          call error_document('missing_text', out)
        end if
        return
      end if
      if (method == 'POST') then
        call json_read(body, n, kind, text)
        select case (kind)
        case (KEY_TEXT)
          status = 200
          call stats_document(text%data, text%n, out)
        case (KEY_MISSING)
          status = 422
          call error_document('missing_text', out)
        case default
          status = 422
          call error_document('invalid_json', out)
        end select
        return
      end if
      status = 405
      call error_document('method_not_allowed', out)
      return
    end if

    status = 404
    call bytes_init(out, 96)
    call put_ascii(out, '{"error":"not_found","detail":"no route for ')
    block
      integer(c_int8_t), allocatable :: text_bytes(:)
      integer :: i
      allocate (text_bytes(len(method)))
      do i = 1, len(method)
        text_bytes(i) = int(iachar(method(i:i)), c_int8_t)
      end do
      call json_escape(text_bytes, len(method), out)
      call put_ascii(out, ' ')
      deallocate (text_bytes)
      allocate (text_bytes(len(target)))
      do i = 1, len(target)
        text_bytes(i) = int(iachar(target(i:i)), c_int8_t)
      end do
      call json_escape(text_bytes, len(target), out)
      deallocate (text_bytes)
    end block
    call put_ascii(out, '"}')
  end subroutine route

end module contract_m
