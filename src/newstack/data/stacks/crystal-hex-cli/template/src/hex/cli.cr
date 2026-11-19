require "./dump"
require "./options"

module Hex
  module CLI
    PROGRAM = "{{ npm_name }}"

    def self.run(args : Array(String), stdout : IO, stderr : IO, stdin : IO = STDIN) : Int32
      parsed = Options.parse(args)
      case parsed.status
      when Options::Status::Help
        stdout.print Options.usage(PROGRAM)
        return 0
      when Options::Status::Version
        stdout.puts "0.1.0"
        return 0
      when Options::Status::UsageError
        stderr.puts "error: #{parsed.message}"
        return 2
      end

      files = parsed.files.empty? ? ["-"] : parsed.files
      files.each do |path|
        data =
          if path == "-"
            stdin.gets_to_end
          else
            begin
              File.read(path)
            rescue
              stderr.puts "error: cannot open '#{path}'"
              return 1
            end
          end
        if parsed.mode == Options::Mode::Dump
          stdout.print Dump.dump(data, parsed.offset, parsed.width)
        else
          bytes = Dump.undump(data)
          stdout.write(bytes)
        end
      end
      0
    end
  end
end