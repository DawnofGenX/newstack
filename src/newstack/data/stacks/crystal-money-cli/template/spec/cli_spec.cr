require "./spec_helper"

describe Money::Cli do
  it "prints the usage and exits 0 for --help" do
    output = IO::Memory.new
    errors = IO::Memory.new
    Money::Cli.run(["--help"], IO::Memory.new(""), output, errors).should eq(0)
    output.to_s.should contain("usage: ")
    errors.to_s.should eq("")
  end

  it "prints the version" do
    output = IO::Memory.new
    Money::Cli.run(["--version"], IO::Memory.new(""), output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("0.1.0")
  end

  it "adds two amounts" do
    output = IO::Memory.new
    status = Money::Cli.run(["add", "USD 1.50", "USD 2.25"], IO::Memory.new(""), output, IO::Memory.new)
    status.should eq(0)
    output.to_s.strip.should eq("USD 3.75")
  end

  it "subtracts and scales" do
    output = IO::Memory.new
    Money::Cli.run(["sub", "USD 10.00", "USD 0.25"], IO::Memory.new(""), output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("USD 9.75")

    output = IO::Memory.new
    Money::Cli.run(["scale", "USD 1.05", "3"], IO::Memory.new(""), output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("USD 3.15")
  end

  it "sums stdin, ignoring comments and blank lines" do
    input = IO::Memory.new("USD 1.00\n\n# opening balance\nUSD 0.50\n")
    output = IO::Memory.new
    Money::Cli.run(["sum"], input, output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("USD 1.50")
  end

  it "reports bad amounts and exits 1" do
    errors = IO::Memory.new
    status = Money::Cli.run(["add", "USD 1.00", "nonsense"], IO::Memory.new(""), IO::Memory.new, errors)
    status.should eq(1)
    errors.to_s.should contain("error: cannot read 'nonsense'")
  end

  it "reports a wrong argument count and exits 2" do
    errors = IO::Memory.new
    Money::Cli.run(["add", "USD 1.00"], IO::Memory.new(""), IO::Memory.new, errors).should eq(2)
    errors.to_s.should contain("expected 2 argument(s), got 1")
  end

  it "reports an unknown command and exits 2" do
    errors = IO::Memory.new
    Money::Cli.run(["frobnicate"], IO::Memory.new(""), IO::Memory.new, errors).should eq(2)
    errors.to_s.should contain("unknown command 'frobnicate'")
  end

  it "splits an amount across ratios" do
    output = IO::Memory.new
    Money::Cli.run(["split", "USD 10.00", "1", "2"], IO::Memory.new(""), output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("USD 3.34 USD 6.66")
  end

  it "shows an amount with its symbol" do
    output = IO::Memory.new
    Money::Cli.run(["show", "USD 12.34"], IO::Memory.new(""), output, IO::Memory.new).should eq(0)
    output.to_s.strip.should eq("$12.34")
  end
end
