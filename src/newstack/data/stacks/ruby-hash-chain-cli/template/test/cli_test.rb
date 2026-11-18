# frozen_string_literal: true

require 'test_helper'
require 'hash_chain/cli'
require 'fileutils'
require 'json'
require 'stringio'
require 'tmpdir'

class CLITest < Minitest::Test
  def setup
    @dir = Dir.mktmpdir('hash-chain')
    @store = File.join(@dir, 'chain.ndjson')
    @stdout = StringIO.new
    @stderr = StringIO.new
  end

  def teardown
    FileUtils.remove_entry(@dir) if File.exist?(@dir)
  end

  def run_cli(*argv, now: 1_700_000_000)
    cli = HashChain::CLI.new(stdin: StringIO.new, stdout: @stdout, stderr: @stderr, now: -> { now })
    cli.run([*argv, '--file', @store])
  end

  def test_append_prints_a_digest_and_writes_the_file
    assert_equal 0, run_cli('append', '{"a":1}')
    assert_match(/\A[0-9a-f]{64}\n\z/, @stdout.string)
    assert File.exist?(@store)
  end

  def test_appends_chain_onto_each_other
    run_cli('append', '{"a":1}')
    first = @stdout.string.strip
    @stdout.truncate(0)
    @stdout.rewind
    run_cli('append', '{"a":2}', now: 1_700_000_500)
    second = @stdout.string.strip

    refute_equal first, second
    @stdout.truncate(0)
    @stdout.rewind
    assert_equal 0, run_cli('head')
    assert_equal second, @stdout.string.strip
  end

  def test_verify_reports_the_entry_count
    run_cli('append', '{"a":1}')
    run_cli('append', '{"a":2}')
    @stdout.truncate(0)
    @stdout.rewind
    assert_equal 0, run_cli('verify')
    assert_equal "ok 2 entries\n", @stdout.string
  end

  def test_verify_fails_loudly_on_hand_edited_history
    run_cli('append', '{"amount":10}')
    text = File.read(@store).sub('"amount":10', '"amount":99')
    File.write(@store, text)

    assert_equal 1, run_cli('verify')
    assert_match(/broken entry 0: digest does not match contents/, @stderr.string)
  end

  def test_head_on_a_missing_file_is_an_error
    assert_equal 1, run_cli('head')
    assert_match(/chain is empty/, @stderr.string)
  end

  def test_show_defaults_to_the_last_entry
    run_cli('append', '{"a":1}')
    run_cli('append', '{"a":2}')
    @stdout.truncate(0)
    @stdout.rewind

    assert_equal 0, run_cli('show')
    entry = JSON.parse(@stdout.string)
    assert_equal 1, entry['seq']
    assert_equal({ 'a' => 2 }, entry['payload'])
  end

  def test_list_prints_every_index
    run_cli('append', '{"a":1}')
    run_cli('append', '{"a":2}')
    @stdout.truncate(0)
    @stdout.rewind

    assert_equal 0, run_cli('list')
    assert_equal %w[0 1], @stdout.string.lines.map { |line| line.split(' ').first }
  end

  def test_a_payload_that_is_not_json_exits_1
    assert_equal 1, run_cli('append', 'not json')
    assert_match(/not valid JSON/, @stderr.string)
  end

  def test_an_unknown_command_exits_2
    assert_equal 2, run_cli('frobnicate')
    assert_match(/unknown command: frobnicate/, @stderr.string)
  end

  def test_help_exits_0_without_touching_the_store
    assert_equal 0, run_cli('--help')
    assert_match(/append PAYLOAD/, @stdout.string)
    refute File.exist?(@store)
  end
end
