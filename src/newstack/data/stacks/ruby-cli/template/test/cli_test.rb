# frozen_string_literal: true

require_relative "test_helper"

class CLITest < Minitest::Test
  def run_cli(argv, stdin: "", files: {})
    stdout = StringIO.new
    stderr = StringIO.new
    reader = ->(path) { files.fetch(path) { raise Errno::ENOENT, path } }
    cli = Textstat::CLI.new(stdin: StringIO.new(stdin), stdout:, stderr:, read_file: reader)
    [cli.run(argv), stdout.string, stderr.string]
  end

  def test_stdin_is_counted_when_no_file_is_named
    status, out, = run_cli([], stdin: "a b\n")
    assert_equal 0, status
    assert_equal "      1      2      4\n", out
  end

  def test_a_dash_means_stdin
    status, out, = run_cli(["-", "-c"], stdin: "héllo wörld\n")
    assert_equal 0, status
    assert_equal "     14\n", out
  end

  def test_a_named_file_is_suffixed_with_its_path
    status, out, = run_cli(["notes.txt"], files: { "notes.txt" => "a b\n" })
    assert_equal 0, status
    assert_equal "      1      2      4 notes.txt\n", out
  end

  def test_several_files_are_counted_in_order
    status, out, = run_cli(["a.txt", "b.txt"], files: { "a.txt" => "x\n", "b.txt" => "y y\n" })
    assert_equal 0, status
    assert_equal ["      1      1      2 a.txt", "      1      2      4 b.txt"], out.lines(chomp: true)
  end

  def test_json_keeps_the_key_order_and_names_the_path
    _status, out, = run_cli(["--json", "a.txt"], files: { "a.txt" => "a b\n" })
    assert_equal %({"lines":1,"words":2,"bytes":4,"path":"a.txt"}\n), out
  end

  def test_a_missing_file_is_reported_and_does_not_stop_the_rest
    status, out, err = run_cli(["gone.txt", "here.txt"], files: { "here.txt" => "x" })
    assert_equal 1, status
    assert_equal "      0      1      1 here.txt\n", out
    assert_match(/gone\.txt: ENOENT/, err)
  end

  def test_a_usage_error_exits_2_and_prints_the_usage_line
    status, out, err = run_cli(["--bogus"])
    assert_equal 2, status
    assert_empty out
    assert_match(/unknown option: --bogus/, err)
    assert_match(/usage: /, err)
  end

  def test_help_exits_0_on_stdout
    status, out, err = run_cli(["--help"])
    assert_equal 0, status
    assert_match(/usage: /, out)
    assert_empty err
  end

  def test_version_exits_0
    status, out, = run_cli(["--version"])
    assert_equal 0, status
    assert_match(/1\.0\.0/, out)
  end
end
