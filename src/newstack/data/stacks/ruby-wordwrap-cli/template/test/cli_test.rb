# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'
require 'tmpdir'

require_relative '../lib/wordwrap/cli'

class CLITest < Minitest::Test
  def run_cli(*argv, stdin: '')
    output = StringIO.new
    error = StringIO.new
    code = Wordwrap::CLI.new(stdin: StringIO.new(stdin), stdout: output, stderr: error).run(argv)
    [output.string, error.string, code]
  end

  def test_standard_input_is_wrapped
    stdout, _, code = run_cli('-w', '7', stdin: 'one two three')
    assert_equal 0, code
    assert_equal "one two\nthree", stdout
  end

  def test_the_default_width_is_used
    stdout, _, code = run_cli(stdin: (['word'] * 40).join(' '))
    assert_equal 0, code
    assert_operator stdout.lines.map(&:chomp).map(&:length).max, :<=, 76
  end

  def test_a_file_is_read
    Dir.mktmpdir do |dir|
      path = File.join(dir, 'in.txt')
      File.write(path, 'one two three')
      stdout, _, code = run_cli('-w', '7', path)
      assert_equal 0, code
      assert_equal "one two\nthree", stdout
    end
  end

  def test_a_missing_file_exits_one
    _, stderr, code = run_cli('/nonexistent/path.txt')
    assert_equal 1, code
    assert_includes stderr, 'cannot read'
  end

  def test_a_zero_width_exits_two
    _, stderr, code = run_cli('-w', '0', stdin: 'a')
    assert_equal 2, code
    assert_includes stderr, 'at least 1'
  end

  def test_an_extra_argument_exits_two
    _, _, code = run_cli('a.txt', 'b.txt')
    assert_equal 2, code
  end

  def test_help_exits_zero
    stdout, _, code = run_cli('--help')
    assert_equal 0, code
    assert_includes stdout, 'usage: {{ npm_name }}'
  end
end
