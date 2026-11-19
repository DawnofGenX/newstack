module Hex
  module Options
    enum Mode
      Dump
      Reverse
    end

    enum Status
      Ok
      Help
      Version
      UsageError
    end

    struct Parsed
      getter mode : Mode
      getter offset : Int32
      getter width : Int32
      getter files : Array(String)
      getter status : Status
      getter message : String

      def initialize(@mode = Mode::Dump, @offset = 0, @width = 16, @files = [] of String,
                     @status = Status::Ok, @message = "")
      end
    end

    VERSION = "0.1.0"

    def self.usage(program : String) : String
      "usage: #{program} [-r] [-o offset] [-w width] [FILE ...]\n" +
        "\n" +
        "Hex dump (default) or reverse with -r.\n"
    end

    def self.parse(args : Array(String)) : Parsed
      mode = Mode::Dump
      offset = 0
      width = 16
      files = [] of String
      i = 0
      while i < args.size
        a = args[i]
        if a == "-h" || a == "--help"
          return Parsed.new(status: Status::Help)
        end
        if a == "-V" || a == "--version"
          return Parsed.new(status: Status::Version)
        end
        if a == "-r" || a == "--reverse"
          mode = Mode::Reverse
          i += 1
          next
        end
        if a == "-o" || a == "--offset"
          offset = args[i+1].to_i32
          i += 2
          next
        end
        if a == "-w" || a == "--width"
          width = args[i+1].to_i32
          i += 2
          next
        end
        if a.starts_with?("-")
          return Parsed.new(status: Status::UsageError, message: "unknown option '#{a}'")
        end
        files << a
        i += 1
      end
      Parsed.new(mode: mode, offset: offset, width: width, files: files, status: Status::Ok)
    end
  end
end