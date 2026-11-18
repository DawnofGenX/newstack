# frozen_string_literal: true

require 'optparse'

require_relative '../base58'

module Base58
  # The command line: arguments in, text out, an exit code returned. Standard
  # input, output and error are injected so the tests never spawn a process.
  class CLI
    USAGE = <<~TEXT
      usage: {{ npm_name }} COMMAND [--text] [VALUE]

      Encode and decode base58, with or without the Base58Check checksum.
      Without VALUE the input is read from standard input. Values are read as
      hex unless --text is given, in which case they are read as UTF-8 text.

        encode         hex bytes -> base58
        decode         base58 -> hex bytes
        check-encode   hex payload -> base58 with a 4-byte checksum
        check-decode   base58 -> hex payload, refusing a bad checksum

      Options:
        -t, --text    read the value as UTF-8 text instead of hex
        -h, --help    show this help and exit

      Exit codes: 0 success, 1 bad input, 2 usage error.
    TEXT

    COMMANDS = %w[encode decode check-encode check-decode].freeze

    class UsageError < StandardError; end

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      options = { text: false, help: false }
      parser = OptionParser.new do |opts|
        opts.on('-t', '--text') { options[:text] = true }
        opts.on('-h', '--help') { options[:help] = true }
      end
      args = parser.parse(argv)

      if options[:help]
        @stdout.print(USAGE)
        return 0
      end

      command = args.shift
      raise UsageError, 'no command given' if command.nil?
      raise UsageError, "unknown command #{command.inspect}" unless COMMANDS.include?(command)
      raise UsageError, "unexpected argument #{args[1].inspect}" if args.length > 1

      value = args.first || @stdin.read.to_s.strip
      raise UsageError, 'no value given on the command line or on standard input' if value.empty?

      @stdout.puts(perform(command, value, options[:text]))
      0
    rescue UsageError => error
      usage_error(error.message)
    rescue Base58::Error, ArgumentError => error
      @stderr.puts("error: #{error.message}")
      1
    end

    private

    def perform(command, value, as_text)
      case command
      when 'encode' then Base58.encode(bytes_for(value, as_text))
      when 'decode' then hex(Base58.decode(value))
      when 'check-encode' then Base58.encode_check(bytes_for(value, as_text))
      when 'check-decode' then hex(Base58.decode_check(value))
      end
    end

    def bytes_for(value, as_text)
      return value.b if as_text

      cleaned = value.gsub(/\s+/, '')
      raise Base58::Error, 'hex input must have an even number of digits' if cleaned.length.odd?
      raise Base58::Error, 'hex input may only contain 0-9a-f' unless cleaned.match?(/\A[0-9a-fA-F]*\z/)

      [cleaned].pack('H*')
    end

    def hex(bytes)
      bytes.unpack1('H*')
    end

    def usage_error(message)
      @stderr.puts("error: #{message}")
      @stderr.puts
      @stderr.print(USAGE)
      2
    end
  end
end
