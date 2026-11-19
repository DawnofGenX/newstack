module Money
  # A command line in, an exit code out. Nothing here calls `exit`; the facade
  # does that, so specs can drive the whole thing.
  module Cli
    PROGRAM = "{{ npm_name }}"

    USAGE = <<-TEXT
      usage: #{PROGRAM} <command> [arguments]

      Amounts are written 'USD 12.34': a three-letter currency, a space, then a
      decimal value with at most two places.

      Commands
        add A B            add two amounts of the same currency
        sub A B            subtract B from A
        sum                add one amount per stdin line
        scale A FACTOR     multiply by a whole number
        split A RATIO...   divide by integer ratios, summing to A
        show A             print A with its currency symbol
        --symbol           used with show: print '$12.34' rather than 'USD 12.34'
        -h, --help         show this message
        -V, --version      show the version

      Exit codes: 0 success, 1 bad amount or input, 2 usage.
    TEXT

    def self.version : String
      "0.1.0"
    end

    # @return [Int32] 0 success, 1 bad input, 2 usage
    def self.run(argv : Array(String), stdin : IO = STDIN, stdout : IO = STDOUT, stderr : IO = STDERR) : Int32
      if argv.empty?
        stderr.puts USAGE
        return 2
      end

      command = argv[0]
      arguments = argv[1..]

      case command
      when "-h", "--help"
        stdout.puts USAGE
        return 0
      when "-V", "--version"
        stdout.puts version
        return 0
      when "add", "sub"
        return expect(arguments, 2, stderr) do
          left = Amount.parse(arguments[0])
          right = Amount.parse(arguments[1])
          result = command == "add" ? left + right : left - right
          stdout.puts result.to_s
        end
      when "scale"
        return expect(arguments, 2, stderr) do
          amount = Amount.parse(arguments[0])
          factor = arguments[1].to_i?
          raise ParseError.new("cannot read '#{arguments[1]}' as a whole number") if factor.nil?
          stdout.puts (amount * factor).to_s
        end
      when "split"
        return expect_at_least(arguments, 2, stderr) do
          amount = Amount.parse(arguments[0])
          ratios = arguments[1..].map do |text|
            ratio = text.to_i?
            raise ParseError.new("cannot read '#{text}' as a ratio") if ratio.nil?
            raise ParseError.new("ratios must not be negative") if ratio < 0
            ratio
          end
          seats = Amount.split(amount, ratios)
          stdout.puts seats.map(&.to_s).join(' ')
          total = seats.reduce(Amount.zero(amount.currency)) { |sum, seat| sum + seat }
          raise ParseError.new("split lost money: #{total} != #{amount}") unless total == amount
        end
      when "sum"
        return run_sum(stdin, stdout, stderr)
      when "show"
        return expect_at_least(arguments, 1, stderr) do
          amount = Amount.parse(arguments[0])
          stdout.puts amount.with_symbol
        end
      else
        stderr.puts "error: unknown command '#{command}'"
        stderr.puts USAGE
        return 2
      end
    rescue error : ParseError
      stderr.puts "error: #{error.message}"
      1
    end

    # Adds one amount per line, ignoring blank lines and '#' comments.
    private def self.run_sum(stdin : IO, stdout : IO, stderr : IO) : Int32
      total = nil.as(Amount?)
      stdin.each_line do |line|
        text = line.strip
        next if text.empty? || text.starts_with?('#')
        amount = Amount.parse(text)
        total = total.nil? ? amount : total.not_nil! + amount
      end
      if total.nil?
        stderr.puts "error: expected at least one amount on stdin"
        return 1
      end
      stdout.puts total.not_nil!.to_s
      0
    end

    private def self.expect(arguments : Array(String), count : Int32, stderr : IO, &block) : Int32
      if arguments.size != count
        stderr.puts "error: expected #{count} argument(s), got #{arguments.size}"
        return 2
      end
      yield
      0
    end

    private def self.expect_at_least(arguments : Array(String), count : Int32, stderr : IO, &block) : Int32
      if arguments.size < count
        stderr.puts "error: expected at least #{count} argument(s), got #{arguments.size}"
        return 2
      end
      yield
      0
    end
  end
end
