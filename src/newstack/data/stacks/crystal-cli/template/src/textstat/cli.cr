# The only place that understands argv, the standard streams and exit codes.
#
# `run` returns the exit code instead of calling `exit`, so specs assert the
# contract without spawning; `src/textstat.cr` turns the value into a process
# status.
require "./counts"
require "./options"

module Textstat
  module CLI
    # The binary name from `shard.yml`'s `targets:` entry, which is the
    # project's `npm_name`. `--help` prints it so the usage line matches the
    # command the user typed.
    PROGRAM = "{{ npm_name }}"

    # Runs one invocation: 0 success (including `--help`/`--version`),
    # 1 an unreadable file, 2 bad usage.
    def self.run(args : Array(String), stdout : IO, stderr : IO, stdin : IO = STDIN) : Int32
      parsed = Options.parse(args)

      case parsed.status
      when Options::Status::Help
        stdout.print Options.usage(PROGRAM)
        return 0
      when Options::Status::Version
        stdout.puts Options::VERSION
        return 0
      when Options::Status::UsageError
        stderr.puts "error: #{parsed.message}"
        stderr.puts
        stderr.print Options.usage(PROGRAM)
        return 2
      end

      if parsed.files.empty?
        print_counts(Counts.of(stdin.gets_to_end), parsed.mode, "", stdout)
        return 0
      end

      total = Counts.new
      failed = false

      parsed.files.each do |path|
        text =
          if path == "-"
            stdin.gets_to_end
          else
            begin
              File.read(path)
            rescue IO::Error
              stderr.puts "error: cannot open '#{path}'"
              failed = true
              next
            end
          end

        counts = Counts.of(text)
        # `-` has no file name to print, like `wc`.
        print_counts(counts, parsed.mode, path == "-" ? "" : path, stdout)
        total = total + counts
      end

      print_counts(total, parsed.mode, "total", stdout) if parsed.files.size > 1
      failed ? 1 : 0
    end

    # Prints the requested figures right-aligned, `wc`-style, then the label.
    private def self.print_counts(counts : Counts, mode : Options::Mode, label : String, io : IO)
      line = String.build do |str|
        str << sprintf("%8d", counts.lines) if mode == Options::Mode::All || mode == Options::Mode::Lines
        str << sprintf("%8d", counts.words) if mode == Options::Mode::All || mode == Options::Mode::Words
        str << sprintf("%8d", counts.bytes) if mode == Options::Mode::All || mode == Options::Mode::Bytes
        unless label.empty?
          str << ' '
          str << label
        end
      end
      io.puts line
    end
  end
end
