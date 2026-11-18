# frozen_string_literal: true

require 'optparse'
require_relative '../pluralize'

module Pluralize
  # Command line front end: plural, singular and count.
  class CLI
    class UsageError < StandardError; end

    # Raised when an input file cannot be read.
    class ReadError < StandardError; end

    COMMANDS = %w[plural singular count].freeze

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      count = nil
      file = nil
      parser = OptionParser.new do |opts|
        opts.banner = 'usage: {{ npm_name }} COMMAND [WORD...] [--count N] [--file PATH]'
        opts.on('-n', '--count N', Integer, 'how many of the word (count command)') { |value| count = value }
        opts.on('-f', '--file PATH', 'read the words from PATH, one per line') { |value| file = value }
        opts.on('-h', '--help', 'print this message') do
          @stdout.puts(opts)
          return 0
        end
      end

      begin
        words = parser.parse(argv)
      rescue OptionParser::ParseError => error
        return usage_error(error.message)
      end

      command = words.shift
      return usage_error('no command given') if command.nil?
      return usage_error("unknown command #{command}") unless COMMANDS.include?(command)

      input = words.empty? ? read_lines(file) : words
      return usage_error('no words given') if input.empty?

      if command == 'count'
        return usage_error('count needs --count N') if count.nil?

        input.each { |word| @stdout.puts(Pluralize.pluralize(count, word)) }
      else
        input.each { |word| @stdout.puts(command == 'plural' ? Pluralize.plural(word) : Pluralize.singular(word)) }
      end
      0
    rescue ReadError => error
      @stderr.puts("#{program}: #{error.message}")
      1
    end

    private

    def program
      '{{ npm_name }}'
    end

    def usage_error(message)
      @stderr.puts("#{program}: #{message}")
      2
    end

    def read_lines(file)
      text = file.nil? ? @stdin.read : File.read(file)
      text.split("\n").map(&:strip).reject(&:empty?)
    rescue SystemCallError => error
      raise ReadError, "cannot read #{file}: #{error.message}"
    end
  end
end
