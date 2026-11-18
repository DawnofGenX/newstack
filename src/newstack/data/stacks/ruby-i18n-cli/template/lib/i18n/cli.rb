#!/usr/bin/env ruby
# frozen_string_literal: true

require 'optparse'
require_relative 'resolver'

module I18n
  class CLI
    PROG = '{{ npm_name }}'

    class UsageError < StandardError; end

    USAGE = <<~TEXT
      usage: #{PROG} [options] KEY
             #{PROG} --check TARGET_LOCALE [options]

      Resolve a locale key with fallback. Options:
        -l, --locale LOCALE   locale to resolve (default: en)
        -d, --dir DIR         directory containing locale YAML files (default: ./locales)
        -c, --check LOCALE    check for keys present in en but missing in LOCALE
        -h, --help            show this help
    TEXT

    def initialize(stdin:, stdout:, stderr:)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      options = { locale: 'en', dir: './locales' }
      check_target = nil
      key = nil

      parser = OptionParser.new do |opts|
        opts.on('-l', '--locale LOCALE') { |v| options[:locale] = v }
        opts.on('-d', '--dir DIR') { |v| options[:dir] = v }
        opts.on('-c', '--check LOCALE') { |v| check_target = v }
        opts.on('-h', '--help') do
          @stdout.print(USAGE)
          return 0
        end
      end

      rest = parser.parse(argv)
      key = rest.first unless rest.empty?

      if check_target
        resolver = Resolver.new(options[:dir])
        missing = resolver.check(check_target)
        if missing.empty?
          @stdout.puts('ok: no missing keys')
          return 0
        end
        missing.each { |k| @stderr.puts("missing: #{k}") }
        return 1
      end

      raise UsageError, 'missing KEY' if key.nil? || key.empty?

      resolver = Resolver.new(options[:dir], default_locale: 'en')
      value = resolver.resolve(key, locale: options[:locale])
      if value.nil? && !resolver.missing?(key, locale: options[:locale])
        # resolved to nil explicitly? treat as missing
      end
      if value.nil? && resolver.missing?(key, locale: options[:locale])
        @stderr.puts("missing key: #{key}")
        return 1
      end
      @stdout.puts(value)
      0
    rescue OptionParser::ParseError => e
      usage_error(e.message)
    rescue UsageError => e
      usage_error(e.message)
    end

    private

    def usage_error(message)
      @stderr.puts("#{PROG}: #{message}")
      @stderr.print(USAGE)
      2
    end
  end
end

if __FILE__ == $PROGRAM_NAME
  cli = I18n::CLI.new(stdin: $stdin, stdout: $stdout, stderr: $stderr)
  exit(cli.run(ARGV))
end
