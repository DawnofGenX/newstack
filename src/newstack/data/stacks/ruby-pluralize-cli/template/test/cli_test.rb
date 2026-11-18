# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'
require 'pluralize/cli'

class CliTest < Minitest::Test
  def run_cli(argv, stdin: '')
    input = StringIO.new(stdin)
    output = StringIO.new
    errors = StringIO.new
    code = Pluralize::CLI.new(stdin: input, stdout: output, stderr: errors).run(argv)
    [code, output.string, errors.string]
  end

  def test_pluralises_arguments
    code, out, = run_cli(%w[plural cat person sheep])
    assert_equal 0, code
    assert_equal "cats\npeople\nsheep\n", out
  end

  def test_singularises_arguments
    code, out, = run_cli(%w[singular cats people boxes])
    assert_equal 0, code
    assert_equal "cat\nperson\nbox\n", out
  end

  def test_reads_stdin_when_no_words_are_given
    code, out, = run_cli(%w[plural], stdin: "baby\nknife\n\n")
    assert_equal 0, code
    assert_equal "babies\nknives\n", out
  end

  def test_count_needs_a_number
    code, _, err = run_cli(%w[count cat])
    assert_equal 2, code
    assert_match(/count needs --count/, err)
  end

  def test_counts_words
    code, out, = run_cli(%w[count --count 2 cat person])
    assert_equal 0, code
    assert_equal "2 cats\n2 people\n", out
  end

  def test_help_exits_zero
    code, out, = run_cli(%w[--help])
    assert_equal 0, code
    assert_match(/usage:/, out)
  end

  def test_unknown_command_and_option_exit_two
    assert_equal 2, run_cli(%w[frobnicate cat])[0]
    assert_equal 2, run_cli(%w[plural --bogus cat])[0]
    assert_equal 2, run_cli([])[0]
  end

  def test_missing_file_exits_one
    code, _, err = run_cli(%w[plural --file does-not-exist.txt])
    assert_equal 1, code
    assert_match(/cannot read/, err)
  end
end
