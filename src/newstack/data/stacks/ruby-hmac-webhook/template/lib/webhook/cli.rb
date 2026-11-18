# frozen_string_literal: true

require 'optparse'
require_relative 'signature'

module Webhook
  # Command line front end. Every stream is injected so the tests never fork.
  class CLI
    PROG = '{{ npm_name }}'

    # Raised when a required flag is absent; run() turns it into exit status 2.
    class UsageError < StandardError; end

    USAGE = <<~TEXT
      usage: #{PROG} sign --secret S (--payload P | --stdin) [--timestamp UNIX]
             #{PROG} verify --secret S --header H (--payload P | --stdin)
                       [--now UNIX] [--tolerance SECONDS]

      sign prints "t=<unix>,v1=<hex>"; verify exits 0 when the header is fresh
      and the digest matches, 1 when it is invalid or expired, 2 on bad usage.
    TEXT

    def initialize(stdin:, stdout:, stderr:, now: Time.now.to_i)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
      @now = now
    end

    def run(argv)
      case argv.first
      when 'sign' then sign(argv.drop(1))
      when 'verify' then verify(argv.drop(1))
      when nil, '-h', '--help', 'help' then print_usage
      else unknown(argv.first)
      end
    rescue OptionParser::ParseError => error
      usage_error(error.message)
    rescue UsageError => error
      usage_error(error.message)
    end

    private

    def unknown(command)
      return usage_error("invalid option #{command}") if command.start_with?('-')

      usage_error("unknown command #{command.inspect}")
    end

    def sign(args)
      options = parse(args, header: false)
      secret = require_option(options, :secret)
      payload = payload_from(options)
      timestamp = options.fetch(:timestamp, @now)

      @stdout.puts(Signature.sign(secret: secret, payload: payload, timestamp: timestamp))
      0
    end

    def verify(args)
      options = parse(args, header: true)
      secret = require_option(options, :secret)
      header = require_option(options, :header)
      payload = payload_from(options)

      result = Signature.verify(
        header: header,
        secret: secret,
        payload: payload,
        now: options.fetch(:now, @now),
        tolerance: options.fetch(:tolerance, Signature::DEFAULT_TOLERANCE)
      )
      return rejection(result) unless result == :ok

      @stdout.puts('ok')
      0
    end

    def rejection(result)
      @stderr.puts(result)
      1
    end

    def parse(args, header:)
      options = {}
      OptionParser.new do |parser|
        parser.on('--secret SECRET') { |value| options[:secret] = value }
        parser.on('--payload PAYLOAD') { |value| options[:payload] = value }
        parser.on('--stdin') { options[:stdin] = true }
        add_mode_options(parser, options, header)
      end.parse!(args)
      options
    end

    def add_mode_options(parser, options, header)
      if header
        parser.on('--header HEADER') { |value| options[:header] = value }
        parser.on('--now UNIX', Integer) { |value| options[:now] = value }
        parser.on('--tolerance SECONDS', Integer) { |value| options[:tolerance] = value }
      else
        parser.on('--timestamp UNIX', Integer) { |value| options[:timestamp] = value }
      end
    end

    def payload_from(options)
      return @stdin.read if options[:stdin]

      require_option(options, :payload)
    end

    def require_option(options, key)
      value = options[key]
      return value unless value.nil? || value.empty?

      raise UsageError, "missing --#{key}"
    end

    def print_usage
      @stdout.print(USAGE)
      0
    end

    def usage_error(message)
      @stderr.puts("#{PROG}: #{message}")
      @stderr.print(USAGE)
      2
    end
  end
end
