# frozen_string_literal: true

require 'optparse'

require_relative '../semver'

module Semver
  class CLI
    USAGE = <<~TEXT
      usage: {{ npm_name }} COMMAND [VERSION ...]

      Parse, validate and compare semantic versions (SemVer 2.0.0).

        compare A B     print -1, 0 or 1
        validate V     print "valid" or "invalid" and exit 0/1
        sort V ...     print versions in ascending order
        bump V LEVEL   bump major|minor|patch

      Options:
        -h, --help    show this help and exit

      Exit codes: 0 success, 1 bad input, 2 usage error.
    TEXT

    COMMANDS = %w[compare validate sort bump].freeze

    class UsageError < StandardError; end

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      options = { help: false }
      parser = OptionParser.new do |opts|
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

      case command
      when 'compare'
        raise UsageError, 'compare needs two versions' unless args.length == 2
        a = Semver.parse(args[0])
        b = Semver.parse(args[1])
        @stdout.puts(Semver.compare(a, b))
      when 'validate'
        raise UsageError, 'validate needs a version' unless args.length == 1
        if Semver.valid?(args[0])
          @stdout.puts('valid')
        else
          @stdout.puts('invalid')
          return 1
        end
      when 'sort'
        raise UsageError, 'sort needs at least one version' if args.empty?
        versions = args.map { |v| Semver.parse(v) }
        versions.sort.each { |v| @stdout.puts(v.to_s) }
      when 'bump'
        raise UsageError, 'bump needs a version and a level' unless args.length == 2
        v = Semver.parse(args[0])
        level = args[1]
        raise UsageError, "unknown level #{level.inspect}" unless %w[major minor patch].include?(level)
        case level
        when 'major' then v.major += 1; v.minor = 0; v.patch = 0; v.pre = nil
        when 'minor' then v.minor += 1; v.patch = 0; v.pre = nil
        when 'patch' then v.patch += 1; v.pre = nil
        end
        @stdout.puts(v.to_s)
      end
      0
    rescue UsageError => error
      usage_error(error.message)
    rescue Semver::Error, ArgumentError => error
      @stderr.puts("error: #{error.message}")
      1
    end

    private

    def usage_error(message)
      @stderr.puts("error: #{message}")
      @stderr.puts
      @stderr.print(USAGE)
      2
    end
  end
end