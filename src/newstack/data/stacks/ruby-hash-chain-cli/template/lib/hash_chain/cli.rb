# frozen_string_literal: true

require 'json'
require 'optparse'
require 'hash_chain'

module HashChain
  # argv -> exit code. All I/O is injected so the tests never touch the real
  # terminal, and the default store is a file next to the caller's cwd.
  class CLI
    DEFAULT_STORE = 'chain.ndjson'

    # Raised anywhere in the command path; #run turns it into exit code 2.
    class UsageError < StandardError; end

    USAGE = <<~TEXT
      Usage: {{ npm_name }} COMMAND [options]

      An append-only hash chain: each entry commits to the digest of the one
      before it, so tampering with history is detectable.

      Commands:
        append PAYLOAD      append a JSON payload and print the new digest
        verify              check the whole chain and print its length
        head                print the digest of the last entry
        show [INDEX]        print one entry as JSON (default: the last one)
        list                print "INDEX DIGEST" for every entry

      Options:
        -f, --file PATH     chain file (default: #{DEFAULT_STORE})
        -a, --at EPOCH      timestamp for `append` (default: now)
        -h, --help          show this help and exit
    TEXT

    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr, now: -> { Time.now.to_i })
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
      @now = now
    end

    def run(argv)
      options = { file: DEFAULT_STORE, at: nil }
      parser = build_parser(options)
      args = parse(argv, parser, options)
      return 0 if args.nil?

      command = args.shift
      case command
      when nil then raise UsageError, 'a command is required'
      when 'append' then append(args, options)
      when 'verify' then verify(options)
      when 'head' then head(options)
      when 'show' then show(args, options)
      when 'list' then list(options)
      else raise UsageError, "unknown command: #{command}"
      end
    rescue UsageError => e
      usage_error(e.message)
    end

    private

    def build_parser(options)
      OptionParser.new do |opts|
        opts.on('-f', '--file PATH', String) { |value| options[:file] = value }
        opts.on('-a', '--at EPOCH', Integer) { |value| options[:at] = value }
        opts.on('-h', '--help') { @stdout.puts(USAGE); options[:help] = true }
      end
    end

    def parse(argv, parser, options)
      args = parser.parse(argv.dup)
      return nil if options[:help]

      args
    rescue OptionParser::ParseError => e
      raise UsageError, e.message
    end

    def usage_error(message)
      @stderr.puts("#{PROGRAM}: #{message}")
      @stderr.puts(USAGE)
      2
    end

    def load_chain(file)
      Chain.parse(File.exist?(file) ? File.read(file) : '')
    end

    def save_chain(file, chain)
      File.write(file, chain.to_ndjson)
    end

    def append(args, options)
      payload_text = args.shift
      raise UsageError, 'append needs a JSON payload' if payload_text.nil?
      raise UsageError, "append takes one payload, got #{args.length + 1}" unless args.empty?

      payload = JSON.parse(payload_text)
      chain = load_chain(options[:file])
      entry = chain.append(payload, at: options[:at] || @now.call)
      save_chain(options[:file], chain)
      @stdout.puts(entry.digest)
      0
    rescue JSON::ParserError => e
      @stderr.puts("#{PROGRAM}: payload is not valid JSON: #{e.message}")
      1
    rescue SystemCallError => e
      @stderr.puts("#{PROGRAM}: cannot write #{options[:file]}: #{e.message}")
      1
    end

    def verify(options)
      chain = load_chain(options[:file])
      ok, error = chain.verify
      if ok
        @stdout.puts("ok #{chain.length} entries")
        0
      else
        @stderr.puts("broken #{error.message}")
        1
      end
    rescue SystemCallError => e
      @stderr.puts("#{PROGRAM}: cannot read #{options[:file]}: #{e.message}")
      1
    end

    def head(options)
      chain = load_chain(options[:file])
      return error_out('chain is empty') if chain.empty?

      @stdout.puts(chain.head)
      0
    end

    def show(args, options)
      chain = load_chain(options[:file])
      return error_out('chain is empty') if chain.empty?

      index = args.empty? ? chain.length - 1 : Integer(args.shift)
      entry = chain.entries[index]
      return error_out("no entry at index #{index}") if entry.nil?

      @stdout.puts(JSON.generate({ 'seq' => entry.seq, 'at' => entry.at, 'payload' => entry.payload,
                                   'prev' => entry.prev, 'digest' => entry.digest }))
      0
    rescue ArgumentError
      raise UsageError, 'index must be an integer'
    end

    def list(options)
      chain = load_chain(options[:file])
      chain.entries.each { |entry| @stdout.puts("#{entry.seq} #{entry.digest}") }
      0
    end

    def error_out(message)
      @stderr.puts("#{PROGRAM}: #{message}")
      1
    end

    PROGRAM = File.basename($PROGRAM_NAME)
  end
end
