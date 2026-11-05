require "./spec_helper"

describe {{ class_name }} do
  it "counts lines, words and bytes" do
    counts = {{ class_name }}.count_text("hello world\n")
    counts.lines.should eq 1
    counts.words.should eq 2
    counts.bytes.should eq 12
  end

  it "returns zeroes for an empty string" do
    counts = {{ class_name }}.count_text("")
    counts.lines.should eq 0
    counts.words.should eq 0
    counts.bytes.should eq 0
  end

  it "counts blank lines without counting words" do
    counts = {{ class_name }}.count_text("\n\nx\n")
    counts.lines.should eq 3
    counts.words.should eq 1
    counts.bytes.should eq 4
  end

  it "counts whitespace as bytes but not words" do
    counts = {{ class_name }}.count_text("  \t ")
    counts.lines.should eq 0
    counts.words.should eq 0
    counts.bytes.should eq 4
  end

  it "measures bytes rather than characters" do
    counts = {{ class_name }}.count_text("héllo wörld\n")
    counts.lines.should eq 1
    counts.words.should eq 2
    counts.bytes.should eq 14
  end

  it "counts an astral character as four bytes" do
    counts = {{ class_name }}.count_text("🙂\n")
    counts.lines.should eq 1
    counts.words.should eq 1
    counts.bytes.should eq 5
  end

  it "counts a trailing run without a newline as one word" do
    counts = {{ class_name }}.count_text("abc")
    counts.lines.should eq 0
    counts.words.should eq 1
    counts.bytes.should eq 3
  end
end
