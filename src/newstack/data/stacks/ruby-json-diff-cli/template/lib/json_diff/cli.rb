# frozen_string_literal: true

require 'optparse'

require_relative '../json_diff'

module JsonDiff
  class CLI
    USAGE = <<~TEXT
      usage: {{ npm_name }} diff LEFT RIGHT

      Deep-diff two JSON documents (files or inline JSON).

      Options:
        -h, --help    show this help and exit

      Exit codes: 0 no differences, 1 differences found or bad input, 2 usage error.
    TEXT

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

      args.shift if args.first == 'diff'
      raise UsageError, 'diff needs two arguments' unless args.length == 2

      left = load(args[0])
      right = load(args[1])
      changes = JsonDiff.diff(left, right)
      if changes.empty?
        @stdout.puts('no differences')
        0
      else
        changes.each { |c| @stdout.puts(c.to_s) }
        1
      end
    rescue UsageError => error
      usage_error(error.message)
    rescue JsonDiff::Error, JSON::ParserError, Errno::ENOENT => error
      @stderr.puts("error: #{error.message}")
      1
    end

    private

    def load(spec)
      File.exist?(spec) ? File.read(spec) : spec
    end

    def usage_error(message)
      @stderr.puts("error: #{message}")
      @stderr.puts
      @stderr.print(USAGE)
      2
    end
  end
end