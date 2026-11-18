# frozen_string_literal: true

require_relative 'test_helper'

class CLITest < Minitest::Test
  DIGEST = '2f441ba4b3b2d50d28a9ab9d9fd8880376ecd1eb5d0435401553f5d8d0a5dcf8'
  PAYLOAD = '{"id":1}'
  NOW = 1_700_000_000

  def run_cli(argv, stdin: '')
    stdout = StringIO.new
    stderr = StringIO.new
    cli = Webhook::CLI.new(stdin: StringIO.new(stdin), stdout: stdout, stderr: stderr, now: NOW)
    [cli.run(argv), stdout.string, stderr.string]
  end

  def test_sign_prints_the_pinned_header
    status, out, = run_cli(['sign', '--secret', 'whsec_test', '--payload', PAYLOAD,
                            '--timestamp', '1700000000'])
    assert_equal 0, status
    assert_equal "t=1700000000,v1=#{DIGEST}\n", out
  end

  def test_sign_defaults_to_the_injected_clock
    status, out, = run_cli(['sign', '--secret', 'whsec_test', '--payload', PAYLOAD])
    assert_equal 0, status
    assert_equal "t=#{NOW},v1=#{DIGEST}\n", out
  end

  def test_sign_reads_the_payload_from_stdin
    status, out, = run_cli(['sign', '--secret', 'whsec_test', '--stdin', '--timestamp',
                            '1700000000'], stdin: PAYLOAD)
    assert_equal 0, status
    assert_equal "t=1700000000,v1=#{DIGEST}\n", out
  end

  def test_verify_accepts_a_good_header
    status, out, err = run_cli(['verify', '--secret', 'whsec_test', '--payload', PAYLOAD,
                                '--header', "t=1700000000,v1=#{DIGEST}"])
    assert_equal 0, status
    assert_equal "ok\n", out
    assert_empty err
  end

  def test_verify_rejects_a_tampered_signature
    status, out, err = run_cli(['verify', '--secret', 'whsec_test', '--payload', PAYLOAD,
                                '--header', "t=1700000000,v1=#{'0' * 64}"])
    assert_equal 1, status
    assert_empty out
    assert_equal "invalid\n", err
  end

  def test_verify_rejects_a_stale_timestamp
    stale = NOW - 400
    digest = Webhook::Signature.digest('whsec_test', stale, PAYLOAD)
    status, _out, err = run_cli(['verify', '--secret', 'whsec_test', '--payload', PAYLOAD,
                                 '--header', "t=#{stale},v1=#{digest}"])
    assert_equal 1, status
    assert_equal "expired\n", err
  end

  def test_an_unknown_command_is_a_usage_error
    status, out, err = run_cli(['frobnicate'])
    assert_equal 2, status
    assert_empty out
    assert_includes err, 'unknown command'
  end

  def test_an_unknown_flag_is_a_usage_error
    status, _out, err = run_cli(['--bogus'])
    assert_equal 2, status
    assert_includes err, 'invalid option'
  end

  def test_a_missing_secret_is_a_usage_error
    status, _out, err = run_cli(['sign', '--payload', PAYLOAD])
    assert_equal 2, status
    assert_includes err, 'missing --secret'
  end

  def test_a_missing_payload_is_a_usage_error
    status, _out, err = run_cli(['sign', '--secret', 'whsec_test'])
    assert_equal 2, status
    assert_includes err, 'missing --payload'
  end

  def test_help_goes_to_stdout_and_exits_zero
    status, out, = run_cli(['--help'])
    assert_equal 0, status
    assert_includes out, 'usage:'
  end
end
