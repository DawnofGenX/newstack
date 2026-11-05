module server_m
  ! Sockets straight from libc through ISO_C_BINDING: Fortran has no networking in
  ! its standard library, so this module declares socket/bind/listen/accept/recv/
  ! send/close and speaks HTTP/1.1 over a plain int8 buffer.
  use, intrinsic :: iso_c_binding, only: c_int, c_int8_t, c_int64_t, c_ptr, c_loc, c_null_ptr
  use bytes_m, only: bytes, bytes_init, bytes_put, bytes_put_str, bytes_put_int, bytes_as_string
  use contract_m, only: route
  implicit none
  private

  public :: serve

  integer, parameter :: AF_INET = 2, SOCK_STREAM = 1, SOL_SOCKET = 1, SO_REUSEADDR = 2
  integer, parameter :: MAX_REQUEST = 65536

  interface
    function c_socket(domain, kind, protocol) bind(c, name="socket") result(fd)
      import :: c_int
      integer(c_int), value :: domain, kind, protocol
      integer(c_int) :: fd
    end function c_socket

    function c_bind(fd, addr, length) bind(c, name="bind") result(rc)
      import :: c_int, c_ptr
      integer(c_int), value :: fd, length
      type(c_ptr), value :: addr
      integer(c_int) :: rc
    end function c_bind

    function c_listen(fd, backlog) bind(c, name="listen") result(rc)
      import :: c_int
      integer(c_int), value :: fd, backlog
      integer(c_int) :: rc
    end function c_listen

    function c_accept(fd, addr, length) bind(c, name="accept") result(client)
      import :: c_int, c_ptr
      integer(c_int), value :: fd
      type(c_ptr), value :: addr, length
      integer(c_int) :: client
    end function c_accept

    function c_recv(fd, buffer, length, flags) bind(c, name="recv") result(got)
      import :: c_int, c_int64_t, c_ptr
      integer(c_int), value :: fd, length, flags
      type(c_ptr), value :: buffer
      integer(c_int64_t) :: got
    end function c_recv

    function c_send(fd, buffer, length, flags) bind(c, name="send") result(sent)
      import :: c_int, c_int64_t, c_ptr
      integer(c_int), value :: fd, length, flags
      type(c_ptr), value :: buffer
      integer(c_int64_t) :: sent
    end function c_send

    function c_close(fd) bind(c, name="close") result(rc)
      import :: c_int
      integer(c_int), value :: fd
      integer(c_int) :: rc
    end function c_close

    function c_setsockopt(fd, level, option, value, length) bind(c, name="setsockopt") result(rc)
      import :: c_int, c_ptr
      integer(c_int), value :: fd, level, option, length
      type(c_ptr), value :: value
      integer(c_int) :: rc
    end function c_setsockopt
  end interface

contains

  subroutine listen_on(fd, port)
    integer(c_int), intent(out) :: fd
    integer, intent(in) :: port
    integer(c_int8_t), target :: address(16)
    integer(c_int), target :: one
    integer(c_int) :: rc

    fd = c_socket(AF_INET, SOCK_STREAM, 0)
    if (fd < 0) then
      write (*, '(A)') 'cannot create a socket'
      stop 1
    end if
    one = 1
    rc = c_setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, c_loc(one), 4_c_int)
    ! sockaddr_in built byte by byte: family 2 (host order short), port in network
    ! order, 127.0.0.1, then 8 bytes of padding. No struct layout to guess.
    address = 0_c_int8_t
    address(1) = 2_c_int8_t
    address(2) = 0_c_int8_t
    address(3) = int(iand(port / 256, 255), c_int8_t)
    address(4) = int(iand(port, 255), c_int8_t)
    address(5) = 127_c_int8_t
    address(6) = 0_c_int8_t
    address(7) = 0_c_int8_t
    address(8) = 1_c_int8_t
    rc = c_bind(fd, c_loc(address), 16_c_int)
    if (rc /= 0) then
      write (*, '(A, I0)') 'cannot bind port ', port
      stop 1
    end if
    rc = c_listen(fd, 16_c_int)
    if (rc /= 0) then
      write (*, '(A)') 'cannot listen'
      stop 1
    end if
  end subroutine listen_on

  function value_at(buf, index) result(value)
    integer(c_int8_t), intent(in) :: buf(:)
    integer, intent(in) :: index
    integer :: value
    value = iand(int(buf(index)), 255)
  end function value_at

  function lowered(value) result(lower)
    integer, intent(in) :: value
    integer :: lower
    lower = value
    if (value >= 65 .and. value <= 90) lower = value + 32
  end function lowered

  function content_length(buf, head_len) result(length)
    integer(c_int8_t), intent(in) :: buf(:)
    integer, intent(in) :: head_len
    integer :: length
    character(len=15), parameter :: wanted = 'content-length:'
    integer :: i, j, value
    logical :: match

    length = 0
    if (head_len < len(wanted)) return
    do i = 1, head_len - len(wanted) + 1
      match = .true.
      do j = 1, len(wanted)
        if (lowered(value_at(buf, i + j - 1)) /= iachar(wanted(j:j))) then
          match = .false.
          exit
        end if
      end do
      if (match) then
        j = i + len(wanted)
        do while (j <= head_len)
          value = value_at(buf, j)
          if (value /= 32 .and. value /= 9) exit
          j = j + 1
        end do
        do while (j <= head_len)
          value = value_at(buf, j)
          if (value < 48 .or. value > 57) exit
          length = length * 10 + (value - 48)
          j = j + 1
        end do
        return
      end if
    end do
  end function content_length

  subroutine read_request(client, buf, total, head_len, body_len, ok)
    integer(c_int), intent(in) :: client
    integer(c_int8_t), target, intent(inout) :: buf(:)
    integer, intent(out) :: total, head_len, body_len
    logical, intent(out) :: ok
    integer(c_int64_t) :: got
    integer :: i, need

    total = 0
    head_len = 0
    body_len = 0
    ok = .false.
    do
      if (total >= size(buf)) return
      got = c_recv(client, c_loc(buf(total + 1)), int(size(buf) - total, c_int), 0_c_int)
      if (got <= 0) return
      total = total + int(got)
      if (head_len == 0) then
        do i = 4, total
          if (value_at(buf, i - 3) == 13 .and. value_at(buf, i - 2) == 10 .and. &
              value_at(buf, i - 1) == 13 .and. value_at(buf, i) == 10) then
            head_len = i
            exit
          end if
        end do
      end if
      if (head_len > 0) then
        body_len = content_length(buf, head_len)
        need = head_len + body_len
        if (total >= need) then
          ok = .true.
          return
        end if
      end if
    end do
  end subroutine read_request

  function reason(status) result(text)
    integer, intent(in) :: status
    character(len=:), allocatable :: text
    select case (status)
    case (200)
      text = 'OK'
    case (404)
      text = 'Not Found'
    case (405)
      text = 'Method Not Allowed'
    case default
      text = 'Unprocessable Entity'
    end select
  end function reason

  subroutine handle(client, buf)
    integer(c_int), intent(in) :: client
    integer(c_int8_t), target, intent(inout) :: buf(:)
    integer :: total, head_len, body_len, status, sent
    character(len=:), allocatable :: head, method, target
    type(bytes) :: out, response
    integer(c_int8_t), allocatable, target :: wire(:)
    logical :: ok
    integer(c_int64_t) :: wrote

    call read_request(client, buf, total, head_len, body_len, ok)
    if (.not. ok) return

    allocate (character(len=head_len) :: head)
    head = transfer(buf(1:head_len), head)
    call split_request(head, method, target)
    if (len(target) == 0) return

    call route(method, target, buf(head_len + 1:head_len + body_len), body_len, status, out)

    call bytes_init(response, size(out%data) + 128)
    call bytes_put_str(response, 'HTTP/1.1 ')
    call bytes_put_int(response, status)
    call bytes_put_str(response, ' ' // reason(status) // '')
    call bytes_put_str(response, char(13) // char(10) // 'content-type: application/json' // &
                                 char(13) // char(10) // 'content-length: ')
    call bytes_put_int(response, out%n)
    call bytes_put_str(response, char(13) // char(10) // 'connection: close' // &
                                 char(13) // char(10) // char(13) // char(10))
    if (out%n > 0) then
      response%data(response%n + 1:response%n + out%n) = out%data(1:out%n)
      response%n = response%n + out%n
    end if

    allocate (wire(response%n))
    wire(1:response%n) = response%data(1:response%n)
    sent = 0
    do while (sent < response%n)
      wrote = c_send(client, c_loc(wire(sent + 1)), int(response%n - sent, c_int), 0_c_int)
      if (wrote <= 0) exit
      sent = sent + int(wrote)
    end do
    deallocate (wire)
  end subroutine handle

  subroutine split_request(head, method, target)
    character(len=*), intent(in) :: head
    character(len=:), allocatable, intent(out) :: method, target
    integer :: first, second
    first = index(head, ' ')
    if (first == 0) then
      method = ''
      target = ''
      return
    end if
    second = index(head(first + 1:), ' ')
    if (second == 0) then
      method = ''
      target = ''
      return
    end if
    method = head(1:first - 1)
    target = head(first + 1:first + second - 1)
  end subroutine split_request

  subroutine serve(port)
    integer, intent(in) :: port
    integer(c_int) :: listener, client
    integer(c_int8_t), target, allocatable :: buf(:)

    call listen_on(listener, port)
    allocate (buf(MAX_REQUEST))
    do
      client = c_accept(listener, c_null_ptr, c_null_ptr)
      if (client < 0) cycle
      call handle(client, buf)
      client = c_close(client)
    end do
  end subroutine serve

end module server_m
