# Command line parsing: argv in, a `Parsed` value out. No I/O, no `exit`, so
# every branch is a unit test rather than a subprocess.
module Textstat
  module Options
    # Which figures to print; `All` prints lines, words and bytes.
    enum Mode
      All
      Lines
      Words
      Bytes
    end

    # How parsing ended, which decides the exit code in `Textstat::CLI`.
    enum Status
      Ok
      Help
      Version
      UsageError
    end

    struct Parsed
      # The chosen mode; defaults to `All`.
      getter mode : Mode
      # Files to read, in order; `-` means standard input.
      getter files : Array(String)
      # Outcome of parsing.
      getter status : Status
      # Error text for `UsageError`, empty otherwise.
      getter message : String

      def initialize(@mode : Mode = Mode::All, @files : Array(String) = [] of String,
                     @status : Status = Status::Ok, @message : String = "")
      end
    end

    VERSION = "0.1.0"

    # The help text. The caller passes the program name so it matches the
    # binary that is actually running.
    def self.usage(program : String) : String
      "usage: #{program} [-l | -w | -c] [--] [FILE ...]\n" +
        "\n" +
        "Count lines, words and bytes in each FILE, or in standard input\n" +
        "when no FILE is given. With more than one FILE a total is printed.\n" +
        "\n" +
        "  -l, --lines     print the line count only\n" +
        "  -w, --words     print the word count only\n" +
        "  -c, --bytes     print the byte count only\n" +
        "  -h, --help      show this help and exit\n" +
        "  -V, --version   show the version and exit\n"
    end

    # Parses `args` without the program name.
    #
    # Hand-rolled instead of `OptionParser` because the parser must stay a
    # pure function: no printing, no exit, so each branch is asserted in
    # `spec/options_spec.cr`.
    def self.parse(args : Array(String)) : Parsed
      mode = Mode::All
      files = [] of String
      chosen = false
      options_ended = false

      args.each do |arg|
        if options_ended || arg.empty? || arg == "-"
          files << arg
          next
        end

        if arg == "--"
          options_ended = true
          next
        end

        if arg == "-h" || arg == "--help"
          return Parsed.new(mode: mode, files: files, status: Status::Help)
        end

        if arg == "-V" || arg == "--version"
          return Parsed.new(mode: mode, files: files, status: Status::Version)
        end

        requested = mode_for(arg)
        unless requested.nil?
          if chosen && mode != requested
            return Parsed.new(
              mode: mode,
              files: files,
              status: Status::UsageError,
              message: "choose one of -l, -w, -c: '#{arg}' conflicts with an earlier mode",
            )
          end
          chosen = true
          mode = requested
          next
        end

        if arg.starts_with?('-')
          return Parsed.new(
            mode: mode,
            files: files,
            status: Status::UsageError,
            message: "unknown option '#{arg}'",
          )
        end

        files << arg
      end

      Parsed.new(mode: mode, files: files, status: Status::Ok)
    end

    private def self.mode_for(arg : String) : Mode?
      case arg
      when "-l", "--lines" then Mode::Lines
      when "-w", "--words" then Mode::Words
      when "-c", "--bytes" then Mode::Bytes
      end
    end
  end
end
