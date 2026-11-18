# frozen_string_literal: true

require 'json'
require 'optparse'

module JsonPath
  class CLI
    PROG = '{{ npm_name }}'

    # Exit codes: 0 matched, 1 nothing matched, 2 usage, 3 unreadable or invalid input.
    USAGE = <<~TEXT
      usage: #{PROG} QUERY [FILE]
             #{PROG} --help

      QUERY is a JSONPath subset: $, .name, ['name'], [0], [-1], .*, [*], ..name, ..*
      Input is read from FILE, or stdin when FILE is absent or -.
      Exit status: 0 when something matched, 1 when nothing did, 2 bad usage, 3 bad input.
    TEXT

    def initialize(stdin:, stdout:, stderr:)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      options = parse_options(argv)
      query = options[:query]
      return 0 if query == :help
      return 2 if query.nil?

      document = read_document(options[:file])
      return 3 if document.nil?

      begin
        matches = Query.query(document, query)
      rescue QueryError => error
        @stderr.puts("error: #{error.message}")
        return 2
      end

      matches.each { |match| @stdout.puts(JSON.generate(match)) }
      @stdout.puts("matched #{matches.length}") if options[:count]
      matches.empty? ? 1 : 0
    end

    private

    def parse_options(argv)
      options = { file: nil, count: false, query: nil }
      parser = OptionParser.new do |opts|
        opts.banner = USAGE
        opts.on('-c', '--count', 'also report how many values matched') { options[:count] = true }
        opts.on('-h', '--help', 'print this help') do
          @stdout.puts(USAGE)
          options[:query] = :help
        end
      end
      rest = parser.parse(argv)
      return options if options[:query] == :help

      options[:query] = rest.first
      options[:file] = rest[1]
      if options[:query].nil?
        @stderr.puts(USAGE)
        return {}
      end
      if rest.length > 2
        @stderr.puts("error: too many arguments: #{rest[2..].join(' ')}")
        @stderr.puts(USAGE)
        return {}
      end
      options
    rescue OptionParser::ParseError => error
      @stderr.puts("error: #{error.message}")
      @stderr.puts(USAGE)
      {}
    end

    def read_document(path)
      raw =
        if path.nil? || path == '-'
          @stdin.read
        elsif File.file?(path)
          begin
            File.read(path)
          rescue SystemCallError => error
            @stderr.puts("error: #{error.message}")
            return nil
          end
        else
          @stderr.puts("error: no such file: #{path}")
          return nil
        end

      JSON.parse(raw)
    rescue JSON::ParserError => error
      @stderr.puts("error: invalid JSON: #{error.message.lines.first&.strip}")
      nil
    end
  end
end
