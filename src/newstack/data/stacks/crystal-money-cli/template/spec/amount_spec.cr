require "./spec_helper"

describe Money::Amount do
  it "reads a currency and a decimal value" do
    amount = Money::Amount.parse("USD 12.34")
    amount.minor.should eq(1234_i64)
    amount.currency.should eq("USD")
    amount.to_s.should eq("USD 12.34")
  end

  it "pads a single decimal place and accepts a whole number" do
    Money::Amount.parse("EUR 5.5").minor.should eq(550_i64)
    Money::Amount.parse("EUR 7").minor.should eq(700_i64)
  end

  it "accepts thousands separators and negatives" do
    Money::Amount.parse("USD 1,234.56").minor.should eq(123_456_i64)
    Money::Amount.parse("USD -0.05").minor.should eq(-5_i64)
    Money::Amount.parse("USD -0.05").to_s.should eq("USD -0.05")
  end

  it "lowercases currency input" do
    Money::Amount.parse("inr 1.00").currency.should eq("INR")
  end

  it "refuses nonsense" do
    expect_raises(Money::ParseError) { Money::Amount.parse("") }
    expect_raises(Money::ParseError) { Money::Amount.parse("12.34") }
    expect_raises(Money::ParseError) { Money::Amount.parse("USD 1.234") }
    expect_raises(Money::ParseError) { Money::Amount.parse("XYZ 1.00") }
    expect_raises(Money::ParseError) { Money::Amount.parse("USD 1.00 extra") }
  end

  it "adds, subtracts and scales without floats" do
    ten = Money::Amount.parse("USD 10.00")
    two_fifty = Money::Amount.parse("USD 2.50")
    (ten + two_fifty).to_s.should eq("USD 12.50")
    (ten - two_fifty).to_s.should eq("USD 7.50")
    (two_fifty * 4).to_s.should eq("USD 10.00")
    (ten + two_fifty).should eq(Money::Amount.parse("USD 12.50"))
  end

  it "refuses to mix currencies" do
    expect_raises(Money::ParseError) do
      Money::Amount.parse("USD 1.00") + Money::Amount.parse("EUR 1.00")
    end
  end

  it "formats with a symbol when one is known" do
    Money::Amount.parse("USD 12.34").with_symbol.should eq("$12.34")
    Money::Amount.parse("USD -12.30").with_symbol.should eq("-$12.30")
    Money::Amount.parse("CHF 3.00").with_symbol.should eq("CHF 3.00")
  end

  it "splits by ratios so the parts add back up" do
    amount = Money::Amount.parse("USD 0.10")
    parts = Money::Amount.split(amount, [1, 1, 1])
    parts.map(&.to_s).should eq(["USD 0.04", "USD 0.03", "USD 0.03"])
    parts.reduce(Money::Amount.zero("USD")) { |sum, part| sum + part }.should eq(amount)
  end

  it "splits negative amounts without losing a minor unit" do
    amount = Money::Amount.parse("EUR -0.10")
    parts = Money::Amount.split(amount, [2, 1])
    parts.map(&.to_s).should eq(["EUR -0.07", "EUR -0.03"])
    parts.reduce(Money::Amount.zero("EUR")) { |sum, part| sum + part }.should eq(amount)
  end

  it "refuses impossible ratios" do
    amount = Money::Amount.parse("USD 1.00")
    expect_raises(Money::ParseError) { Money::Amount.split(amount, [] of Int32) }
    expect_raises(Money::ParseError) { Money::Amount.split(amount, [0, 0]) }
    expect_raises(Money::ParseError) { Money::Amount.split(amount, [-1, 2]) }
  end
end
