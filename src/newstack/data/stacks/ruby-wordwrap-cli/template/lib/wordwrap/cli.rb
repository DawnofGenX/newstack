# frozen_string_literal: true

require 'optparse'

require_relative '../wordwrap'

module Wordwrap
  # Arguments in, text out, exit code returned. Input and output are injected so
  # the tests never spawn a process or touch the real streams.
  class CLI
    USAGE = <<~TEXT
      usage: {{ npm_name }} [-w WIDTH] [FILE]

      Reflow text so every line fits in WIDTH columns (default #{DEFAULT_WIDTH}).
      Blank lines separate paragraphs; newlines inside a paragraph are treated as
      spaces, so running the tool twice gives the same text. A word longer than
      the width is left intact rather than split.

      Options:
        -w, --width WIDTH   target line width, at least 1
        -h, --help          show this help and exit

      With no FILE, text is read from standard input.
      Exit codes: 0 success, 1 unreadable input, 2 usage error.
    TEXT

    class UsageError < StandardError; end
    # Raised when the named file cannot be read, which is a different failure
    # from a bad command line: exit 1, not 2.
    class ReadError < StandardError; end

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      width = DEFAULT_WIDTH
      help = false
      parser = OptionParser.new do |opts|
        opts.on('-w', '--width WIDTH', Integer) { |value| width = value }
        opts.on('-h', '--help') { help = true }
      end
      files = parser.parse(argv)

      if help
        @stdout.print(USAGE)
        return 0
      end
      raise UsageError, "unexpected argument #{files[1].inspect}" if files.length > 1
      raise UsageError, 'width must be at least 1' unless width.positive?

      @stdout.print(Wordwrap.wrap(read(files.first), width: width))
      0
    rescue UsageError => error
      usage_error(error.message)
    rescue ReadError => error
      @stderr.puts("error: #{error.message}")
      1
    rescue Wordwrap::Error, ArgumentError => error
      @stderr.puts("error: #{error.message}")
      2
    end

    private

    def read(path)
      return @stdin.read if path.nil? || path == '-'

      File.read(path)
    rescue SystemCallError => error
      raise ReadError, "cannot read #{path}: #{error.message}"
    end

    def usage_error(message)
      @stderr.puts("error: #{message}")
      @stderr.puts
      @stderr.print(USAGE)
      2
    end
  end
end
