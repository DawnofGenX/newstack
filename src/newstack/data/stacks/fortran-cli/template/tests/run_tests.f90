module harness
  !! A forty-line test harness instead of a dependency: count the checks,
  !! name every failure, exit non-zero when anything failed.
  use textstat_counts, only: counts_t
  implicit none
  integer :: passed = 0
  integer :: failed = 0

contains

  subroutine check(name, condition, detail)
    character(len=*), intent(in) :: name
    logical, intent(in) :: condition
    character(len=*), intent(in), optional :: detail
    if (condition) then
      passed = passed + 1
    else
      failed = failed + 1
      write (*, '(A)') 'FAIL ' // name
      if (present(detail)) write (*, '(A)') '     ' // detail
    end if
  end subroutine check

  subroutine check_counts(name, got, want_lines, want_words, want_bytes)
    character(len=*), intent(in) :: name
    type(counts_t), intent(in) :: got
    integer, intent(in) :: want_lines
    integer, intent(in) :: want_words
    integer, intent(in) :: want_bytes
    character(len=96) :: detail
    write (detail, '(A,I0,A,I0,A,I0,A,I0,A,I0,A,I0)') 'got ', got%lines, '/', got%words, &
      '/', got%bytes, ' want ', want_lines, '/', want_words, '/', want_bytes
    call check(name, got%lines == want_lines .and. got%words == want_words &
      .and. got%bytes == want_bytes, detail)
  end subroutine check_counts
end module harness

module fixtures
  use iso_fortran_env, only: int8
  implicit none

contains

  subroutine write_bytes(path, text)
    character(len=*), intent(in) :: path
    character(len=*), intent(in) :: text
    integer :: unit, i
    integer(int8) :: b
    open (newunit=unit, file=path, access='stream', form='unformatted', status='replace')
    do i = 1, len(text)
      b = int(iachar(text(i:i)), int8)
      write (unit) b
    end do
    close (unit)
  end subroutine write_bytes
end module fixtures

program run_tests
  use iso_fortran_env, only: int8
  use harness
  use fixtures
  use textstat_counts, only: counter_t, counts_t, counts_add, is_space_byte
  use textstat_options, only: options_t, parse_options, status_ok, status_help, &
    status_version, status_usage
  use textstat_runner, only: run, program_name
  implicit none

  type(counter_t) :: counter
  type(counts_t) :: first
  type(counts_t) :: second
  type(options_t) :: opts
  character(len=16), dimension(0) :: no_args
  integer :: unit, err_unit, code, ios
  character(len=256) :: line1, line2, line3

  call count_tests()
  call option_tests()
  call runner_tests()

  write (*, '(A,I0,A,I0,A,I0)') 'checks: ', passed + failed, ', passed: ', passed, &
    ', failed: ', failed
  if (failed > 0) then
    call exit(1)
  end if
  call exit(0)

contains

  subroutine feed_text(target, text)
    type(counter_t), intent(inout) :: target
    character(len=*), intent(in) :: text
    integer :: i
    call target%reset()
    do i = 1, len(text)
      call target%feed(int(iachar(text(i:i)), int8))
    end do
  end subroutine feed_text

  subroutine count_tests()
    call feed_text(counter, 'alpha beta' // new_line('a') // 'gamma' // new_line('a'))
    call check_counts('two lines of words', counter%value(), 2, 3, 17)

    call feed_text(counter, '')
    call check_counts('empty input', counter%value(), 0, 0, 0)

    call feed_text(counter, 'abc')
    call check_counts('no trailing newline', counter%value(), 0, 1, 3)

    call feed_text(counter, 'a' // achar(9) // 'b' // achar(11) // 'c' // achar(12) // 'd' // new_line('a'))
    call check_counts('tab, vertical tab and form feed separate words', counter%value(), 1, 4, 8)

    call feed_text(counter, '  ' // new_line('a') // new_line('a'))
    call check_counts('whitespace only', counter%value(), 2, 0, 4)

    call feed_text(counter, 'alpha' // new_line('a'))
    first = counter%value()
    call feed_text(counter, 'beta' // new_line('a') // 'gamma' // new_line('a'))
    second = counter%value()
    call check_counts('counts add', counts_add(first, second), 3, 3, 17)
    call check_counts('adding nothing changes nothing', counts_add(first, counts_t()), 1, 1, 6)

    call check('32 is whitespace', is_space_byte(32_int8))
    call check('9 is whitespace', is_space_byte(9_int8))
    call check('1 is not whitespace', .not. is_space_byte(1_int8))
    call check('a letter is not whitespace', .not. is_space_byte(65_int8))
  end subroutine count_tests

  subroutine option_tests()
    opts = parse_options(no_args)
    call check('no flags means every figure', opts%show_lines .and. opts%show_words &
      .and. opts%show_bytes)
    call check('no operands means no files', size(opts%files) == 0)
    call check('the status is ok', opts%status == status_ok)

    opts = parse_options([character(len=16) :: '-l'])
    call check('-l is lines only', opts%show_lines .and. .not. opts%show_words &
      .and. .not. opts%show_bytes)

    opts = parse_options([character(len=16) :: '--words'])
    call check('--words is words only', opts%show_words .and. .not. opts%show_lines)

    opts = parse_options([character(len=16) :: '-lw'])
    call check('clustered -lw', opts%show_lines .and. opts%show_words &
      .and. .not. opts%show_bytes)

    opts = parse_options([character(len=16) :: '-h'])
    call check('-h asks for help', opts%status == status_help)
    opts = parse_options([character(len=16) :: '--help'])
    call check('--help asks for help', opts%status == status_help)
    opts = parse_options([character(len=16) :: '-V'])
    call check('-V asks for the version', opts%status == status_version)
    opts = parse_options([character(len=16) :: '--version'])
    call check('--version asks for the version', opts%status == status_version)

    opts = parse_options([character(len=16) :: '--bogus'])
    call check('--bogus is a usage error', opts%status == status_usage)
    call check('the message names the option', &
      index(opts%message, 'unknown option: --bogus') > 0, opts%message)

    opts = parse_options([character(len=16) :: '-x'])
    call check('-x is a usage error', opts%status == status_usage)

    opts = parse_options([character(len=16) :: 'a.txt', 'b.txt'])
    call check('two operands', size(opts%files) == 2)
    call check('operands keep their order', opts%files(1) == 'a.txt' .and. opts%files(2) == 'b.txt')

    opts = parse_options([character(len=16) :: '-lw', 'a.txt'])
    call check('a flag before an operand still counts it', size(opts%files) == 1)

    opts = parse_options([character(len=16) :: '-'])
    call check('- is an operand', size(opts%files) == 1 .and. opts%files(1) == '-')

    opts = parse_options([character(len=16) :: '--', '-l'])
    call check('-- makes the rest operands', size(opts%files) == 1 .and. opts%files(1) == '-l')
  end subroutine option_tests

  subroutine fresh_scratch()
    ! One file for stdout, another for stderr: the runner writes the file-level
    ! complaint to stderr first, so sharing a unit would interleave the rows.
    ! Explicit files instead of status='scratch': a scratch file has to be
    ! deleted when its unit closes, and gfortran refuses with "File cannot be
    ! deleted" on filesystems that will not unlink an open file.
    close (unit)
    close (err_unit)
    open (newunit=unit, file='build/verify-out.txt', status='replace', action='readwrite')
    open (newunit=err_unit, file='build/verify-err.txt', status='replace', action='readwrite')
  end subroutine fresh_scratch

  subroutine runner_tests()
    call write_bytes('build/fixture1.txt', 'alpha beta' // new_line('a') // 'gamma' // new_line('a'))
    call write_bytes('build/fixture2.txt', 'delta' // new_line('a'))
    call write_bytes('build/empty.txt', '')

    call fresh_scratch()
    code = run([character(len=64) :: 'build/fixture1.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('one file exits zero', code == 0)
    call check('one file prints one row', line1 == ' 2  3 17 build/fixture1.txt', line1)
    read (unit, '(A)', iostat=ios) line2
    call check('one file prints no total', ios /= 0)

    call fresh_scratch()
    code = run([character(len=64) :: 'build/fixture1.txt', 'build/fixture2.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    read (unit, '(A)', iostat=ios) line2
    read (unit, '(A)', iostat=ios) line3
    call check('two files exit zero', code == 0)
    call check('first row', line1 == ' 2  3 17 build/fixture1.txt', line1)
    call check('second row', line2 == ' 1  1  6 build/fixture2.txt', line2)
    call check('total row', line3 == ' 3  4 23 total', line3)

    call fresh_scratch()
    code = run([character(len=64) :: '-l', 'build/fixture1.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('-l prints the newline count alone', line1 == '2 build/fixture1.txt', line1)

    call fresh_scratch()
    code = run([character(len=64) :: 'build/empty.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('an empty file is three zeroes', line1 == '0 0 0 build/empty.txt', line1)

    call fresh_scratch()
    code = run([character(len=64) :: 'build/missing.txt'], unit, err_unit)
    rewind (err_unit)
    read (err_unit, '(A)', iostat=ios) line1
    call check('a missing file exits one', code == 1)
    call check('the message names the file', line1 == "error: cannot open 'build/missing.txt'", line1)

    call fresh_scratch()
    code = run([character(len=64) :: 'build/missing1.txt', 'build/missing2.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('two missing files still print a total', line1 == '0 0 0 total', line1)
    call check('two missing files exit one', code == 1)

    call fresh_scratch()
    code = run([character(len=64) :: 'build/fixture1.txt', 'build/missing.txt'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    read (unit, '(A)', iostat=ios) line2
    call check('a partial failure still prints the total', line2 == ' 2  3 17 total', line2)
    call check('a partial failure exits one', code == 1)

    call fresh_scratch()
    code = run([character(len=64) :: '--help'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('--help exits zero', code == 0)
    call check('--help explains itself', index(line1, 'Count lines, words and bytes') == 1, line1)

    call fresh_scratch()
    code = run([character(len=64) :: '--version'], unit, err_unit)
    rewind (unit)
    read (unit, '(A)', iostat=ios) line1
    call check('--version exits zero', code == 0)
    call check('--version prints the version', line1 == '0.1.0', line1)

    call fresh_scratch()
    code = run([character(len=64) :: '--bogus'], unit, err_unit)
    rewind (err_unit)
    read (err_unit, '(A)', iostat=ios) line1
    read (err_unit, '(A)', iostat=ios) line2
    call check('an unknown option exits two', code == 2)
    call check('the first line names the option', &
      line1 == program_name // ': unknown option: --bogus', line1)
    call check('the second line points at --help', &
      line2 == "Try '" // program_name // " --help' for more information.", line2)

    close (unit, status='delete')
    close (err_unit, status='delete')
  end subroutine runner_tests

end program run_tests
