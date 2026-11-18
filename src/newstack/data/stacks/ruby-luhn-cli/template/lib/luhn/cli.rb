# frozen_string_literal: true

require 'optparse'

module Luhn
  class CLI
    PROG = '{{ npm_name }}'

    class UsageError < StandardError; end

    USAGE = <<~TEXT
      usage: #{PROG} validate NUMBER
             #{PROG} generate PREFIX
             #{PROG} brand NUMBER
    TEXT

    def initialize(stdin:, stdout:, stderr:)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      command = argv.first
      case command
      when nil, '-h', '--help', 'help' then print_usage
      when 'validate' then validate(argv.drop(1))
      when 'generate' then generate(argv.drop(1))
      when 'brand' then brand(argv.drop(1))
      else
        unknown(command)
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

    def validate(args)
      number = require_arg(args, 'NUMBER')
      if Checksum.valid?(number)
        @stdout.puts('valid')
        0
      else
        @stdout.puts('invalid')
        1
      end
    end

    def generate(args)
      prefix = require_arg(args, 'PREFIX')
      @stdout.puts(Checksum.generate(prefix))
      0
    end

    def brand(args)
      number = require_arg(args, 'NUMBER')
      @stdout.puts(Checksum.brand(number))
      0
    end

    def require_arg(args, label)
      value = args.first
      raise UsageError, "missing #{label}" if value.nil? || value.empty?

      value
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
