# frozen_string_literal: true

require 'test_helper'
require 'json'
require 'stringio'
require 'tempfile'

class CliTest < Minitest::Test
  DOCUMENT = { 'a' => [{ 'b' => 1 }, { 'b' => 2 }], 'c' => 'x' }.freeze

  def run_cli(argv, stdin: '')
    stdout = StringIO.new
    stderr = StringIO.new
    status = JsonPath::CLI.new(stdin: StringIO.new(stdin), stdout: stdout, stderr: stderr).run(argv)
    [status, stdout.string, stderr.string]
  end

  def test_prints_each_match_as_json
    status, out, = run_cli(['$.a[*].b'], stdin: JSON.generate(DOCUMENT))
    assert_equal 0, status
    assert_equal ['1', '2'], out.lines.map(&:strip)
  end

  def test_no_match_exits_one
    status, out, = run_cli(['$.nope'], stdin: JSON.generate(DOCUMENT))
    assert_equal 1, status
    assert_empty out
  end

  def test_count_flag_appends_the_total
    status, out, = run_cli(['--count', '$.a[*].b'], stdin: JSON.generate(DOCUMENT))
    assert_equal 0, status
    assert_equal 'matched 2', out.lines.last.strip
  end

  def test_reads_a_file
    file = Tempfile.new(['doc', '.json'])
    file.write(JSON.generate(DOCUMENT))
    file.flush
    status, out, = run_cli(['$.c', file.path])
    assert_equal 0, status
    assert_equal '"x"', out.strip
  ensure
    file&.close!
  end

  def test_invalid_json_exits_three
    status, _out, err = run_cli(['$'], stdin: '{not json')
    assert_equal 3, status
    assert_match(/invalid JSON/, err)
  end

  def test_missing_file_exits_three
    status, _out, err = run_cli(['$', 'does-not-exist.json'])
    assert_equal 3, status
    assert_match(/no such file/, err)
  end

  def test_bad_query_exits_two
    status, _out, err = run_cli(['book'], stdin: '{}')
    assert_equal 2, status
    assert_match(/must start with \$/, err)
  end

  def test_no_arguments_prints_usage_and_exits_two
    status, _out, err = run_cli([], stdin: '{}')
    assert_equal 2, status
    assert_match(/usage:/, err)
  end

  def test_help_exits_zero
    status, out, = run_cli(['--help'])
    assert_equal 0, status
    assert_match(/usage:/, out)
  end
end
