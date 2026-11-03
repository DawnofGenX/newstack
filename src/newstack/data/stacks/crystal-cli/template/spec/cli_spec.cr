require "./spec_helper"

# The exit-code contract is only real if the compiled binary is what exits, so
# this suite builds `src/textstat.cr` once and runs it as a child process
# instead of calling `Textstat::CLI.run` and trusting its return value.
module SpecBinary
  extend self

  @@path : String?

  def path : String
    cached = @@path
    return cached if cached

    bin = File.join(Dir.tempdir, "textstat-spec-#{Process.pid}")
    status = Process.run(
      "crystal",
      ["build", "-o", bin, "src/textstat.cr"],
      output: Process::Redirect::Inherit,
      error: Process::Redirect::Inherit,
    )
    raise "crystal build of src/textstat.cr failed" unless status.success?
    at_exit { File.delete(bin) if File.exists?(bin) }
    @@path = bin
    bin
  end
end

private def run_binary(args : Array(String), input : String = "") : {String, String, Int32}
  stdout = IO::Memory.new
  stderr = IO::Memory.new
  stdin = IO::Memory.new(input)
  status = Process.run(SpecBinary.path, args, output: stdout, error: stderr, input: stdin)
  {stdout.to_s, stderr.to_s, status.exit_code}
end

private def with_fixture(name : String, contents : String, &)
  path = File.join(Dir.tempdir, "textstat-#{Process.pid}-#{name}")
  File.write(path, contents)
  begin
    yield path
  ensure
    File.delete(path) if File.exists?(path)
  end
end

describe "textstat binary" do
  it "prints usage naming the built binary and exits 0 for --help" do
    out, _err, code = run_binary(["--help"])
    code.should eq 0
    out.should start_with "usage: {{ npm_name }} "
    out.should contain "--lines"
  end

  it "exits 0 for --version" do
    out, _err, code = run_binary(["-V"])
    code.should eq 0
    out.strip.should eq "0.1.0"
  end

  it "exits 2 for an unknown flag and explains it on stderr" do
    out, err, code = run_binary(["--bogus"])
    code.should eq 2
    out.should be_empty
    err.should contain "unknown option '--bogus'"
    err.should contain "usage: {{ npm_name }}"
  end

  it "exits 2 for conflicting modes" do
    _out, err, code = run_binary(["-l", "-c"])
    code.should eq 2
    err.should contain "conflicts"
  end

  it "exits 1 for a file that cannot be read" do
    _out, err, code = run_binary(["does-not-exist.txt"])
    code.should eq 1
    err.should contain "cannot open 'does-not-exist.txt'"
  end

  it "counts a file with a trailing newline" do
    with_fixture("newline.txt", "hello world\n") do |path|
      out, _err, code = run_binary([path])
      code.should eq 0
      out.strip.split.should eq ["1", "2", "12", path]
    end
  end

  it "does not invent a line for a file without a trailing newline" do
    with_fixture("nonewline.txt", "hello world") do |path|
      out, _err, code = run_binary([path])
      code.should eq 0
      out.strip.split.should eq ["0", "2", "11", path]
    end
  end

  it "prints only the selected figure" do
    with_fixture("words.txt", "one two three\n") do |path|
      out, _err, code = run_binary(["-w", path])
      code.should eq 0
      out.strip.split.should eq ["3", path]
    end
  end

  it "counts standard input when no file is given" do
    out, _err, code = run_binary([] of String, "a b\n")
    code.should eq 0
    out.strip.split.should eq ["1", "2", "4"]
  end

  it "counts standard input for a bare -" do
    out, _err, code = run_binary(["-"], "a b\n")
    code.should eq 0
    out.strip.split.should eq ["1", "2", "4"]
  end

  it "prints a total for several files" do
    with_fixture("a.txt", "a b\n") do |first|
      with_fixture("b.txt", "c\n") do |second|
        out, _err, code = run_binary([first, second])
        code.should eq 0
        lines = out.lines
        lines.size.should eq 3
        lines[0].split.should eq ["1", "2", "4", first]
        lines[1].split.should eq ["1", "1", "2", second]
        lines[2].split.should eq ["2", "3", "6", "total"]
      end
    end
  end

  it "keeps counting other files after a missing one and still exits 1" do
    with_fixture("good.txt", "a b\n") do |good|
      out, err, code = run_binary([good, "does-not-exist.txt"])
      code.should eq 1
      err.should contain "cannot open"
      out.should contain "1"
    end
  end
end
