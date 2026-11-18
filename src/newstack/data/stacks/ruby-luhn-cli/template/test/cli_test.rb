# frozen_string_literal: true

require_relative 'test_helper'

class CLITest < Minitest::Test
  def run_cli(argv)
    stdout = StringIO.new
    stderr = StringIO.new
    cli = Luhn::CLI.new(stdin: StringIO.new, stdout: stdout, stderr: stderr)
    [cli.run(argv), stdout.string, stderr.string]
  end

  def test_validate_valid
    status, out, err = run_cli(['validate', '4111111111111111'])
    assert_equal 0, status
    assert_equal "valid\n", out
    assert_empty err
  end

  def test_validate_invalid
    status, out, err = run_cli(['validate', '4111111111111112'])
    assert_equal 1, status
    assert_equal "invalid\n", out
    assert_empty err
  end

  def test_generate
    status, out, = run_cli(['generate', '411111111111111'])
    assert_equal 0, status
    assert_equal "4111111111111111\n", out
  end

  def test_brand
    status, out, = run_cli(['brand', '4111111111111111'])
    assert_equal 0, status
    assert_equal "visa\n", out
  end

  def test_unknown_command
    status, out, err = run_cli(['frobnicate'])
    assert_equal 2, status
    assert_empty out
    assert_includes err, 'unknown command'
  end

  def test_unknown_flag
    status, _out, err = run_cli(['--bogus'])
    assert_equal 2, status
    assert_includes err, 'invalid option'
  end

  def test_missing_arg
    status, _out, err = run_cli(['validate'])
    assert_equal 2, status
    assert_includes err, 'missing NUMBER'
  end

  def test_help
    status, out, = run_cli(['--help'])
    assert_equal 0, status
    assert_includes out, 'usage:'
  end
end
