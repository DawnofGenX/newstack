# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'

require_relative '../lib/json_diff/cli'

class CLITest < Minitest::Test
  def run_cli(*argv, stdin: '')
    input = StringIO.new(stdin)
    output = StringIO.new
    error = StringIO.new
    code = JsonDiff::CLI.new(stdin: input, stdout: output, stderr: error).run(argv)
    [output.string, error.string, code]
  end

  def test_no_diff_exits_zero
    stdout, _, code = run_cli('diff', '{"a":1}', '{"a":1}')
    assert_equal 0, code
    assert_includes stdout, 'no differences'
  end

  def test_diff_exits_one
    stdout, _, code = run_cli('diff', '{"a":1}', '{"a":2}')
    assert_equal 1, code
    assert_includes stdout, 'a: 1 -> 2'
  end

  def test_no_command_exits_two
    _, _, code = run_cli
    assert_equal 2, code
  end

  def test_help_exits_zero
    stdout, _, code = run_cli('--help')
    assert_equal 0, code
    assert_includes stdout, 'usage: {{ npm_name }}'
  end
end