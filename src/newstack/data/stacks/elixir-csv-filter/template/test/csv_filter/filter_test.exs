defmodule CsvFilter.FilterTest do
  use ExUnit.Case, async: true

  alias CsvFilter.Filter

  test "filters by index" do
    data = "name,age\nalice,30\nbob,25\n"
    assert Filter.filter(data, "1", "alice", false, true) == "name,age\nalice,30\n"
  end

  test "filters by header name" do
    data = "name,age\nalice,30\nbob,25\n"
    assert Filter.filter(data, "name", "bob", false, true) == "name,age\nbob,25\n"
  end

  test "invert" do
    data = "name,age\nalice,30\nbob,25\n"
    assert Filter.filter(data, "1", "alice", true, true) == "name,age\nbob,25\n"
  end

  test "no trailing newline preserved" do
    data = "name,age\nalice,30\nbob,25"
    assert Filter.filter(data, "1", "alice", false, true) == "name,age\nalice,30"
  end
end
