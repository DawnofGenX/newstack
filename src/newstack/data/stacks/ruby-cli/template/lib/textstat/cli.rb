# frozen_string_literal: true

require_relative "counts"
require_relative "options"

module Textstat
  # The whole program as one callable function. Every side effect arrives as a
  # keyword argument, so the tests pass StringIO and never touch a terminal.
  class CLI
    USAGE = <<~TEXT
      usage: {{ npm_name }} [-l] [-w] [-c] [--json] [file ...]

      Counts lines, words and bytes; reads stdin when no file is given or when the
      file is "-". With no flags all three counts are printed, wc-style.

        -l, --lines    lines        -w, --words    words
        -c, --bytes    bytes        --json        one JSON object per file
        -h, --help     this text    -V, --version  the version
    TEXT

    def initialize(stdin:, stdout:, stderr:, read_file: ->(path) { File.binread(path) })
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
      @read_file = read_file
    end

    def run(argv)
      options = Options.parse(argv)
      return show(@stdout, USAGE) if options.help
      return show(@stdout, "{{ npm_name }} #{VERSION}") if options.version

      paths = options.paths.empty? ? ["-"] : options.paths
      status = 0
      paths.each { |path| status |= report(path, options) }
      status
    rescue UsageError => e
      @stderr.puts("{{ npm_name }}: #{e.message}")
      @stderr.puts(USAGE.lines.first)
      2
    end

    private

    def report(path, options)
      text = read(path)
      return 1 if text.nil?

      counts = Textstat.count(text)
      if options.json
        @stdout.puts(json_for(counts, path))
      else
        @stdout.puts(line_for(counts, options, path))
      end
      0
    end

    def read(path)
      return @stdin.read if path == "-"

      @read_file.call(path)
    rescue SystemCallError => e
      @stderr.puts("{{ npm_name }}: #{path}: #{e.class.name.split("::").last}")
      nil
    end

    def line_for(counts, options, path)
      parts = []
      parts << counts.lines.to_s.rjust(7) if options.lines?
      parts << counts.words.to_s.rjust(7) if options.words?
      parts << counts.bytes.to_s.rjust(7) if options.bytes?
      parts << " #{path}" unless path == "-"
      parts.join
    end

    def json_for(counts, path)
      # Hand-built so the key order is the contract, not whatever a library emits.
      counts.to_json.sub(/\}\z/, %(,"path":#{path.inspect}}))
    end

    def show(io, text)
      io.puts(text)
      0
    end
  end
end
