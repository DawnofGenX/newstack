# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'

require_relative '../lib/base58/cli'

class CLITest < Minitest::Test
  def run_cli(*argv, stdin: '')
    input = StringIO.new(stdin)
    output = StringIO.new
    error = StringIO.new
    code = Base58::CLI.new(stdin: input, stdout: output, stderr: error).run(argv)
    [output.string, error.string, code]
  end

  def test_encode_takes_hex
    stdout, _, code = run_cli('encode', '68656c6c6f20776f726c64')
    assert_equal 0, code
    assert_equal "StV1DL6CwTryKyV\n", stdout
  end

  def test_encode_text_mode_reads_utf8
    stdout, _, code = run_cli('encode', '--text', 'hello world')
    assert_equal 0, code
    assert_equal "StV1DL6CwTryKyV\n", stdout
  end

  def test_decode_prints_hex
    stdout, _, code = run_cli('decode', '2g')
    assert_equal 0, code
    assert_equal "61\n", stdout
  end

  def test_check_round_trip_through_the_cli
    stdout, _, code = run_cli('check-encode', '000f9a4b120000000000')
    assert_equal 0, code
    assert_equal "12JNo32w2yrmQuWFckG\n", stdout

    back, _, code = run_cli('check-decode', stdout.strip)
    assert_equal 0, code
    assert_equal "000f9a4b120000000000\n", back
  end

  def test_a_bad_character_exits_one
    _, stderr, code = run_cli('decode', '2g0')
    assert_equal 1, code
    assert_includes stderr, 'invalid base58 character'
  end

  def test_odd_hex_exits_one
    _, stderr, code = run_cli('encode', 'abc')
    assert_equal 1, code
    assert_includes stderr, 'even number of digits'
  end

  def test_no_command_exits_two
    _, stderr, code = run_cli
    assert_equal 2, code
    assert_includes stderr, 'no command given'
  end

  def test_an_unknown_command_exits_two
    _, _, code = run_cli('frobnicate', '2g')
    assert_equal 2, code
  end

  def test_an_extra_argument_exits_two
    _, _, code = run_cli('decode', '2g', 'extra')
    assert_equal 2, code
  end

  def test_help_exits_zero
    stdout, _, code = run_cli('--help')
    assert_equal 0, code
    assert_includes stdout, 'usage: {{ npm_name }}'
  end

  def test_standard_input_is_read_when_no_value_is_given
    stdout, _, code = run_cli('decode', stdin: "2g\n")
    assert_equal 0, code
    assert_equal "61\n", stdout
  end
end
