# frozen_string_literal: true

require 'optparse'
require_relative '../huffman'

module Huffman
  # Command line front end: encode, decode, table and stats.
  class CLI
    class UsageError < StandardError; end

    # Raised when the input file cannot be read.
    class ReadError < StandardError; end

    COMMANDS = %w[encode decode table stats].freeze

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      command = nil
      file = nil
      parser = OptionParser.new do |opts|
        opts.banner = 'usage: {{ npm_name }} COMMAND [FILE]'
        opts.on('-h', '--help', 'print this message') do
          @stdout.puts(opts)
          return 0
        end
      end
      args = parser.parse(argv)
      command = args.shift
      file = args.shift
      raise UsageError, 'no command given' if command.nil?
      raise UsageError, "unknown command #{command.inspect}" unless COMMANDS.include?(command)
      raise UsageError, "unexpected argument #{args.first.inspect}" unless args.empty?

      text = read(file)
      case command
      when 'encode' then @stdout.puts(Huffman.dump(text))
      when 'decode' then @stdout.puts(decode_payload(text))
      when 'table' then print_table(text)
      when 'stats' then print_stats(text)
      end
      0
    rescue UsageError => error
      @stderr.puts("error: #{error.message}")
      @stderr.puts("commands: #{COMMANDS.join(', ')}")
      2
    rescue Huffman::DecodeError, ReadError => error
      @stderr.puts("error: #{error.message}")
      1
    end

    private

    def decode_payload(text)
      bits, table = Huffman.load(text)
      Huffman.decode(bits, table)
    end

    def print_table(text)
      table = Huffman.codes(Huffman.tree_for(text))
      table.sort_by { |symbol, code| [code.length, symbol] }.each do |symbol, code|
        @stdout.puts("#{symbol.inspect}\t#{code}")
      end
    end

    def print_stats(text)
      bits = Huffman.encode(text)
      packed = Huffman.compressed_bytes(text)
      original = text.bytesize
      @stdout.puts("symbols=#{Huffman.frequencies(text).length}")
      @stdout.puts("bits=#{bits.length}")
      @stdout.puts("bytes=#{packed}")
      @stdout.puts("original_bytes=#{original}")
      ratio = original.zero? ? 0.0 : (packed.to_f / original)
      @stdout.puts(format('ratio=%.3f', ratio))
    end

    def read(path)
      return @stdin.read if path.nil? || path == '-'

      File.read(path)
    rescue SystemCallError => error
      raise ReadError, "cannot read #{path}: #{error.message}"
    end
  end
end
