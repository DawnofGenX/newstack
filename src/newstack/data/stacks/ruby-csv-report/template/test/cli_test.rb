# frozen_string_literal: true

require_relative 'test_helper'

class CliTest < Minitest::Test
  def test_runs
    csv = Tempfile.new(['data', '.csv'])
    csv.write("dept,salary\neng,100\nhr,50\n")
    csv.close
    out = StringIO.new
    err = StringIO.new
    code = CsvReport::CLI.new(stdout: out, stderr: err, stdin: StringIO.new).run([csv.path, '--group', 'dept'])
    assert_equal 0, code
    assert out.string.include?('eng')
    assert out.string.include?('"groups"')
  ensure
    csv.unlink
  end
end
