# frozen_string_literal: true

require 'minitest/autorun'

require_relative '../lib/json_diff'

class JsonDiffTest < Minitest::Test
  def test_no_difference
    changes = JsonDiff.diff('{"a":1,"b":[2,3]}', '{"a":1,"b":[2,3]}')
    assert_empty changes
  end

  def test_changed_scalar
    changes = JsonDiff.diff('{"a":1}', '{"a":2}')
    assert_equal 1, changes.length
    assert_equal 'a: 1 -> 2', changes.first.to_s
  end

  def test_added_and_removed
    changes = JsonDiff.diff('{"a":1}', '{"b":2}')
    assert_equal 2, changes.length
  end

  def test_nested_array
    changes = JsonDiff.diff('[1,2,3]', '[1,9,3,4]')
    assert_equal 2, changes.length
  end

  def test_invalid_json_raises
    assert_raises(JsonDiff::Error) { JsonDiff.parse('{bad') }
  end
end