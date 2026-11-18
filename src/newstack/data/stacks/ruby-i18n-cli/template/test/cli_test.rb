# frozen_string_literal: true

require 'test_helper'
require 'tmpdir'
require 'fileutils'

class CliTest < Minitest::Test
  def setup
    @dir = Dir.mktmpdir
    FileUtils.mkdir_p(File.join(@dir, 'locales'))
    File.write(File.join(@dir, 'locales', 'en.yml'), <<~YAML)
      en:
        greeting: Hello
    YAML
    File.write(File.join(@dir, 'locales', 'de.yml'), <<~YAML)
      de:
        greeting: Hallo
    YAML
    @stdin = StringIO.new
    @stdout = StringIO.new
    @stderr = StringIO.new
  end

  def teardown
    FileUtils.rm_rf(@dir)
  end

  def test_resolve
    cli = I18n::CLI.new(stdin: @stdin, stdout: @stdout, stderr: @stderr)
    status = cli.run(['greeting', '-l', 'de', '-d', File.join(@dir, 'locales')])
    assert_equal 0, status
    assert_equal "Hallo\n", @stdout.string
  end

  def test_missing_exits_1
    cli = I18n::CLI.new(stdin: @stdin, stdout: @stdout, stderr: @stderr)
    status = cli.run(['nope', '-l', 'de', '-d', File.join(@dir, 'locales')])
    assert_equal 1, status
    assert_match(/missing key/, @stderr.string)
  end

  def test_check_mode
    cli = I18n::CLI.new(stdin: @stdin, stdout: @stdout, stderr: @stderr)
    status = cli.run(['--check', 'de', '-d', File.join(@dir, 'locales')])
    # en has greeting, de has greeting, no missing -> 0
    assert_equal 0, status
  end

  def test_check_mode_fails_on_missing
    File.write(File.join(@dir, 'locales', 'fr.yml'), "fr:\n  x: 1\n")
    cli = I18n::CLI.new(stdin: @stdin, stdout: @stdout, stderr: @stderr)
    status = cli.run(['--check', 'fr', '-d', File.join(@dir, 'locales')])
    assert_equal 1, status
  end
end
