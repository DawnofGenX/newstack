module selftest_m
  ! No test framework: one function that runs the checks, prints a line per check
  ! and returns the exit code. Everything goes through `route`, so the socket is
  ! the only thing not covered here (the http step covers that).
  !
  ! Fortran has no escape sequences in character constants, so '"\n"' is a
  ! backslash and an n - which is exactly what JSON wants on the way IN. A real
  ! newline on the way OUT is char(10), hence the LF/CR constants below.
  use, intrinsic :: iso_c_binding, only: c_int8_t
  use bytes_m, only: bytes, bytes_init, bytes_put, bytes_as_string
  use contract_m, only: route
  implicit none
  private

  public :: run_selftest

  character(len=*), parameter :: LF = char(10)
  character(len=*), parameter :: CR = char(13)
  character(len=*), parameter :: BS = char(92)

  integer :: failures = 0

contains

  subroutine check(name, ok)
    character(len=*), intent(in) :: name
    logical, intent(in) :: ok
    if (ok) then
      write (*, '(A, A)') 'ok ', name
    else
      failures = failures + 1
      write (*, '(A, A)') 'FAIL ', name
    end if
  end subroutine check

  function as_bytes(text) result(out)
    character(len=*), intent(in) :: text
    integer(c_int8_t), allocatable :: out(:)
    integer :: i
    allocate (out(len(text)))
    do i = 1, len(text)
      out(i) = int(iachar(text(i:i)), c_int8_t)
    end do
  end function as_bytes

  subroutine expect(name, method, target, body, want_status, want_body)
    character(len=*), intent(in) :: name, method, target, want_body
    character(len=*), intent(in) :: body
    integer, intent(in) :: want_status
    integer(c_int8_t), allocatable :: raw(:)
    integer :: status
    type(bytes) :: out
    logical :: ok

    raw = as_bytes(body)
    call route(method, target, raw, size(raw), status, out)
    ok = status == want_status .and. bytes_as_string(out) == want_body
    if (.not. ok) then
      if (status /= want_status) then
        write (*, '(A, A, I0, A, I0)') '  want status ', name, want_status, ' got ', status
      else
        write (*, '(A, A)') '  got ', bytes_as_string(out)
      end if
    end if
    call check(name, ok)
  end subroutine expect

  function run_selftest() result(code)
    integer :: code
    type(bytes) :: out
    integer :: status, n
    integer(c_int8_t), allocatable :: raw(:)

    failures = 0

    call expect('empty text has no counts', 'GET', '/stats?text=', '', 200, &
                '{"text":"","lines":0,"words":0,"bytes":0}')
    call expect('one line is one line', 'GET', '/stats?text=hello%20world%0A', '', 200, &
                '{"text":"hello world' // BS // 'n","lines":1,"words":2,"bytes":12}')
    call expect('no newline means no line', 'GET', '/stats?text=a%20b', '', 200, &
                '{"text":"a b","lines":0,"words":2,"bytes":3}')
    call expect('crlf counts one line', 'GET', '/stats?text=a%0D%0Ab%0D%0A', '', 200, &
                '{"text":"a' // BS // 'r' // BS // 'nb' // BS // 'r' // BS // 'n","lines":2,"words":2,"bytes":6}')
    call expect('utf8 is counted in bytes', 'GET', &
                '/stats?text=h%C3%A9llo%20w%C3%B6rld%0A', '', 200, &
                '{"text":"héllo wörld' // BS // 'n","lines":1,"words":2,"bytes":14}')
    call expect('tabs separate words', 'GET', '/stats?text=a%09b', '', 200, &
                '{"text":"a' // BS // 'tb","lines":0,"words":2,"bytes":3}')
    call expect('vertical tab separates words', 'GET', '/stats?text=a%0Bb', '', 200, &
                '{"text":"a' // BS // 'u000Bb","lines":0,"words":2,"bytes":3}')
    call expect('form feed separates words', 'GET', '/stats?text=a%0Cb', '', 200, &
                '{"text":"a' // BS // 'fb","lines":0,"words":2,"bytes":3}')
    call expect('runs of separators are one gap', 'GET', '/stats?text=%20a%20%20', '', 200, &
                '{"text":" a  ","lines":0,"words":1,"bytes":4}')
    call expect('plus is a space', 'GET', '/stats?text=a+b', '', 200, &
                '{"text":"a b","lines":0,"words":2,"bytes":3}')
    call expect('percent escapes work in the key', 'GET', '/stats?te%78t=a', '', 200, &
                '{"text":"a","lines":0,"words":1,"bytes":1}')
    call expect('the first text wins', 'GET', '/stats?text=a&text=b', '', 200, &
                '{"text":"a","lines":0,"words":1,"bytes":1}')
    call expect('other parameters are ignored', 'GET', '/stats?other=1', '', 422, &
                '{"error":"missing_text"}')
    call expect('a bare stats has no text', 'GET', '/stats', '', 422, &
                '{"error":"missing_text"}')

    call expect('post counts the body', 'POST', '/stats', &
                '{"text":"a b' // BS // 'nc' // BS // 'n"}', 200, &
                '{"text":"a b' // BS // 'nc' // BS // 'n","lines":2,"words":3,"bytes":6}')
    call expect('an escape becomes a newline', 'POST', '/stats', &
                '{"text":"a' // BS // 'nb"}', 200, &
                '{"text":"a' // BS // 'nb","lines":1,"words":2,"bytes":3}')
    call expect('a unicode escape is re-encoded', 'POST', '/stats', &
                '{"text":"caf' // BS // 'u00e9"}', 200, &
                '{"text":"café","lines":0,"words":1,"bytes":5}')
    call expect('a surrogate pair is one code point', 'POST', '/stats', &
                '{"text":"' // BS // 'ud83d' // BS // 'ude00"}', 200, &
                '{"text":"😀","lines":0,"words":1,"bytes":4}')
    call expect('quotes and backslashes are escaped', 'POST', '/stats', &
                '{"text":"a' // BS // '"b' // BS // BS // 'c"}', 200, &
                '{"text":"a' // BS // '"b' // BS // BS // 'c","lines":0,"words":1,"bytes":5}')
    call expect('a missing member is missing text', 'POST', '/stats', '{}', 422, &
                '{"error":"missing_text"}')
    call expect('a number is not text', 'POST', '/stats', '{"text":42}', 422, &
                '{"error":"missing_text"}')
    call expect('a broken document is invalid', 'POST', '/stats', '{', 422, &
                '{"error":"invalid_json"}')
    call expect('an empty body is invalid', 'POST', '/stats', '', 422, &
                '{"error":"invalid_json"}')
    call expect('trailing garbage is invalid', 'POST', '/stats', '{"text":"a"} x', 422, &
                '{"error":"invalid_json"}')
    call expect('an array is not a document', 'POST', '/stats', '[]', 422, &
                '{"error":"invalid_json"}')
    call expect('nested values are skipped', 'POST', '/stats', &
                '{"meta":{"a":[1,2,{"b":null}]},"text":"z"}', 200, &
                '{"text":"z","lines":0,"words":1,"bytes":1}')
    call expect('the last text member wins', 'POST', '/stats', &
                '{"text":"a","text":"b"}', 200, &
                '{"text":"b","lines":0,"words":1,"bytes":1}')
    call expect('health is ok', 'GET', '/health', '', 200, '{"status":"ok"}')
    call expect('health with a query is still health', 'GET', '/health?x=1', '', 200, &
                '{"status":"ok"}')
    call expect('a wrong method on health is 405', 'POST', '/health', '', 405, &
                '{"error":"method_not_allowed"}')
    call expect('a wrong method on stats is 405', 'DELETE', '/stats', '', 405, &
                '{"error":"method_not_allowed"}')
    call expect('an unknown route is 404', 'GET', '/nope', '', 404, &
                '{"error":"not_found","detail":"no route for GET /nope"}')
    call expect('a wrong method on an unknown route is 404', 'DELETE', '/nope', '', 404, &
                '{"error":"not_found","detail":"no route for DELETE /nope"}')
    call expect('routes are case sensitive', 'GET', '/Health', '', 404, &
                '{"error":"not_found","detail":"no route for GET /Health"}')

    raw = as_bytes('{"text":"a"}')
    n = size(raw)
    call route('POST', '/stats', raw, n, status, out)
    call check('a normal post answers 200', status == 200)

    if (failures == 0) then
      write (*, '(A)') 'checks: all passed'
      code = 0
    else
      write (*, '(A, I0)') 'failures: ', failures
      code = 1
    end if
  end function run_selftest

end module selftest_m
