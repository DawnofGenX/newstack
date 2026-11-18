# frozen_string_literal: true

require 'minitest/autorun'
require 'stringio'
require 'tempfile'
require 'huffman/cli'

class HuffmanCliTest < Minitest::Test
  def run_cli(argv, input = '')
    stdout = StringIO.new
    stderr = StringIO.new
    code = Huffman::CLI.new(stdin: StringIO.new(input), stdout: stdout, stderr: stderr).run(argv)
    [code, stdout.string, stderr.string]
  end

  def test_encode_then_decode_round_trips
    code, payload, = run_cli(['encode'], 'abracadabra')
    assert_equal 0, code
    decoded_code, text, = run_cli(['decode'], payload)
    assert_equal 0, decoded_code
    assert_equal "abracadabra\n", text
  end

  def test_encode_prints_the_table_then_the_bits
    _, payload, = run_cli(['encode'], 'aab')
    lines = payload.split("\n")
    assert_equal 2, lines.first.to_i
    assert_equal 4, lines.length
    assert_match(/\A[01]{3}\z/, lines.last)
  end

  def test_table_lists_codes
    code, output, = run_cli(['table'], 'aab')
    assert_equal 0, code
    assert_includes output, '"a"'
    assert_equal 2, output.lines.length
  end

  def test_stats_reports_sizes
    code, output, = run_cli(['stats'], 'aaaaab')
    assert_equal 0, code
    assert_match(/^symbols=2$/, output.lines[0].strip)
    assert_match(/^original_bytes=6$/, output.lines[3].strip)
  end

  def test_unknown_command_exits_2
    code, _, stderr = run_cli(['squash'], 'x')
    assert_equal 2, code
    assert_match(/unknown command/, stderr)
  end

  def test_no_command_exits_2
    code, _, stderr = run_cli([], 'x')
    assert_equal 2, code
    assert_match(/no command given/, stderr)
  end

  def test_help_exits_0
    code, output, = run_cli(['--help'], '')
    assert_equal 0, code
    assert_match(/usage: /, output)
  end

  def test_a_missing_file_exits_1
    code, _, stderr = run_cli(['encode', '/nonexistent/file.txt'])
    assert_equal 1, code
    assert_match(/cannot read/, stderr)
  end

  def test_a_bad_payload_exits_1
    code, _, stderr = run_cli(['decode'], 'not a payload')
    assert_equal 1, code
    assert_match(/error:/, stderr)
  end

  def test_reads_a_named_file
    Tempfile.create(%w[input txt]) do |file|
      file.write('hello hello')
      file.flush
      code, payload, = run_cli(['encode', file.path])
      assert_equal 0, code
      assert_includes payload, '"h"'
    end
  end
end
