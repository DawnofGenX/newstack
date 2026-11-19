require "./spec_helper"

describe Hex::Dump do
  it "dumps bytes" do
    out = Hex::Dump.dump("AB")
    out.should contain("41 42")
  end

  it "round trips" do
    data = "Hello"
    dumped = Hex::Dump.dump(data)
    Hex::Dump.undump(dumped).to_a.should eq(data.bytes)
  end
end
