module Hex
  module Dump
    # stack: crystal-hex-cli
    def self.dump(data : String, offset : Int32 = 0, width : Int32 = 16) : String
      bytes = data.bytes
      io = IO::Memory.new
      pos = 0
      while pos < bytes.size
        slice = bytes[pos, width]
        hex_fields = Array(String).new(width) { "  " }
        slice.each_with_index do |b, j|
          hex_fields[j] = b.to_s(16).rjust(2, '0')
        end
        hex = hex_fields.join(" ")
        ascii = slice.map do |b|
          (32 <= b <= 126) ? b.chr : '.'
        end.join
        ascii = ascii.ljust(width, ' ')
        io.puts sprintf("%08x:  %s  %s", offset + pos, hex, ascii)
        pos += width
      end
      io.to_s
    end

    def self.undump(text : String) : Bytes
      out = IO::Memory.new
      text.each_line do |line|
        parts = line.split("  ")
        hexsection = parts.size > 1 ? parts[1] : parts[0]
        hexsection.split.each do |tok|
          next if tok.ends_with?(":")
          next unless tok =~ /^[0-9a-fA-F]+$/
          i = 0
          while i + 1 < tok.size
            out.write_byte(tok[i, 2].to_u8(16))
            i += 2
          end
        end
      end
      out.to_slice
    end
  end
end