require "./spec_helper"

describe Textstat::Options do
  it "defaults to every figure with no files" do
    parsed = Textstat::Options.parse([] of String)
    parsed.status.should eq Textstat::Options::Status::Ok
    parsed.mode.should eq Textstat::Options::Mode::All
    parsed.files.should eq [] of String
  end

  it "selects lines and keeps the file" do
    parsed = Textstat::Options.parse(["-l", "a.txt"])
    parsed.status.should eq Textstat::Options::Status::Ok
    parsed.mode.should eq Textstat::Options::Mode::Lines
    parsed.files.should eq ["a.txt"]
  end

  it "accepts the long forms" do
    Textstat::Options.parse(["--words"]).mode.should eq Textstat::Options::Mode::Words
    Textstat::Options.parse(["--bytes"]).mode.should eq Textstat::Options::Mode::Bytes
    Textstat::Options.parse(["--lines"]).mode.should eq Textstat::Options::Mode::Lines
  end

  it "allows the same mode twice" do
    Textstat::Options.parse(["-l", "--lines"]).mode.should eq Textstat::Options::Mode::Lines
  end

  it "rejects conflicting modes as a usage error" do
    parsed = Textstat::Options.parse(["-l", "-c"])
    parsed.status.should eq Textstat::Options::Status::UsageError
    parsed.message.should contain "conflicts"
  end

  it "stops at --help" do
    parsed = Textstat::Options.parse(["--help", "-l"])
    parsed.status.should eq Textstat::Options::Status::Help
  end

  it "treats -h as --help" do
    Textstat::Options.parse(["-h"]).status.should eq Textstat::Options::Status::Help
  end

  it "reports --version separately" do
    Textstat::Options.parse(["-V"]).status.should eq Textstat::Options::Status::Version
  end

  it "rejects unknown flags with the flag in the message" do
    parsed = Textstat::Options.parse(["--bogus"])
    parsed.status.should eq Textstat::Options::Status::UsageError
    parsed.message.should contain "unknown option '--bogus'"
  end

  it "ends option parsing at --" do
    parsed = Textstat::Options.parse(["--", "-l"])
    parsed.status.should eq Textstat::Options::Status::Ok
    parsed.mode.should eq Textstat::Options::Mode::All
    parsed.files.should eq ["-l"]
  end

  it "treats a bare - as standard input" do
    parsed = Textstat::Options.parse(["-"])
    parsed.status.should eq Textstat::Options::Status::Ok
    parsed.files.should eq ["-"]
  end

  it "names the real binary in the usage line" do
    Textstat::Options.usage("{{ npm_name }}").should start_with "usage: {{ npm_name }} "
  end
end
