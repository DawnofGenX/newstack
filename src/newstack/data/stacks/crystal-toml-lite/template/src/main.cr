require "./toml_lite"

VERSION = "0.1.0"
PROGRAM = "{{ npm_name }}"

def usage
  "Usage: #{PROGRAM} FILE\n       #{PROGRAM} --help\n       #{PROGRAM} --version\nParse a TOML subset and print flattened key = value lines.\n"
end

if ARGV.empty? || ARGV.includes?("--help") || ARGV.includes?("-h")
  print usage
  exit 0
end
if ARGV.includes?("--version")
  puts VERSION
  exit 0
end
unknown = ARGV.find { |a| a.starts_with?("-") && a != "--help" && a != "-h" && a != "--version" }
if unknown
  STDERR.puts "error: unknown option '#{unknown}'"
  STDERR.puts usage
  exit 2
end
if ARGV.size != 1
  STDERR.puts "error: expected one file"
  STDERR.puts usage
  exit 2
end

path = ARGV[0]
unless File.exists?(path)
  STDERR.puts "error: cannot read '#{path}'"
  exit 1
end

begin
  text = File.read(path)
  parsed = TomlLite.parse(text)
  puts TomlLite.render(parsed)
rescue ex
  STDERR.puts "error: #{ex.message}"
  exit 2
end
