require "./spec_helper"

describe Textstat::Counts do
  it "finds nothing in empty input" do
    Textstat::Counts.of("").should eq Textstat::Counts.new(0, 0, 0)
  end

  it "counts a trailing newline as a line" do
    Textstat::Counts.of("hello\n").should eq Textstat::Counts.new(1, 1, 6)
  end

  it "does not count an unterminated last line, like wc -l" do
    Textstat::Counts.of("hello").should eq Textstat::Counts.new(0, 1, 5)
  end

  it "does not count an empty line after the final newline" do
    Textstat::Counts.of("one two\nthree\n").should eq Textstat::Counts.new(2, 3, 14)
  end

  it "splits words on runs of spaces without counting empty ones" do
    Textstat::Counts.of("  a   b  ").should eq Textstat::Counts.new(0, 2, 9)
  end

  it "treats tab, carriage return, vertical tab and form feed as whitespace" do
    Textstat::Counts.of("\ta\r\nb\v\fc\n").should eq Textstat::Counts.new(2, 3, 9)
  end

  it "counts bytes, not characters, for UTF-8 text" do
    # "héllo" is five characters but six bytes.
    Textstat::Counts.of("héllo").should eq Textstat::Counts.new(0, 1, 6)
  end

  it "adds totals field by field" do
    (Textstat::Counts.of("a b\n") + Textstat::Counts.of("c\n")).should eq Textstat::Counts.new(2, 3, 6)
  end
end
