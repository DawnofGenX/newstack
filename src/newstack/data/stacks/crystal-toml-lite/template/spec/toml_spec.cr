require "./spec_helper"

describe "TomlLite" do
  it "parses flat keys" do
    parsed = TomlLite.parse("name = \"demo\"\ncount = 3\nratio = 1.5\nenabled = true\n")
    parsed["name"].should eq "demo"
    parsed["count"].should eq 3
    parsed["ratio"].should eq 1.5
    parsed["enabled"].should eq true
  end

  it "flattens tables" do
    parsed = TomlLite.parse("[server]\nhost = \"localhost\"\nport = 8080\n")
    parsed["server.host"].should eq "localhost"
    parsed["server.port"].should eq 8080
  end
end
