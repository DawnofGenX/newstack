# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'

require_relative '../lib/semver/cli'

class CLITest < Minitest::Test
  def run_cli(*argv, stdin: '')
    input = StringIO.new(stdin)
    output = StringIO.new
    error = StringIO.new
    code = Semver::CLI.new(stdin: input, stdout: output, stderr: error).run(argv)
    [output.string, error.string, code]
  end

  def test_compare
    stdout, _, code = run_cli('compare', '1.0.0', '2.0.0')
    assert_equal 0, code
    assert_equal "-1\n", stdout
  end

  def test_validate_valid
    stdout, _, code = run_cli('validate', '1.2.3-rc.1')
    assert_equal 0, code
    assert_equal "valid\n", stdout
  end

  def test_validate_invalid
    stdout, _, code = run_cli('validate', '1.2')
    assert_equal 1, code
    assert_equal "invalid\n", stdout
  end

  def test_sort
    stdout, _, code = run_cli('sort', '2.0.0', '1.0.0', '1.5.0')
    assert_equal 0, code
    assert_equal "1.0.0\n1.5.0\n2.0.0\n", stdout
  end

  def test_bump
    stdout, _, code = run_cli('bump', '1.2.3', 'minor')
    assert_equal 0, code
    assert_equal "1.3.0\n", stdout
  end

  def test_no_command_exits_two
    _, _, code = run_cli
    assert_equal 2, code
  end

  def test_unknown_command_exits_two
    _, _, code = run_cli('frobnicate')
    assert_equal 2, code
  end

  def test_help_exits_zero
    stdout, _, code = run_cli('--help')
    assert_equal 0, code
    assert_includes stdout, 'usage: {{ npm_name }}'
  end
end