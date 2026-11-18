# frozen_string_literal: true

require 'test_helper'

class JsonPathTest < Minitest::Test
  STORE = {
    'store' => {
      'book' => [
        { 'title' => 'A', 'price' => 8 },
        { 'title' => 'B', 'price' => 12 },
      ],
      'bicycle' => { 'color' => 'red', 'price' => 19 },
    },
    'expensive' => 10
  }.freeze

  def test_root_returns_the_whole_document
    assert_equal [STORE], JsonPath::Query.query(STORE, '$')
  end

  def test_member_access_by_dot_and_bracket
    assert_equal [STORE['expensive']], JsonPath::Query.query(STORE, '$.expensive')
    assert_equal [STORE['expensive']], JsonPath::Query.query(STORE, "$['expensive']")
  end

  def test_array_indexes_including_negative
    assert_equal ['A'], JsonPath::Query.query(STORE, '$.store.book[0].title')
    assert_equal ['B'], JsonPath::Query.query(STORE, '$.store.book[-1].title')
    assert_empty JsonPath::Query.query(STORE, '$.store.book[9].title')
  end

  def test_wildcards_walk_arrays_and_objects
    assert_equal ['A', 'B'], JsonPath::Query.query(STORE, '$.store.book[*].title')
    assert_equal ['red', 19], JsonPath::Query.query(STORE, '$.store.bicycle.*')
  end

  def test_recursive_descent_finds_every_price
    assert_equal [8, 12, 19], JsonPath::Query.query(STORE, '$..price')
  end

  def test_recursive_wildcard_returns_nested_values
    titles = JsonPath::Query.query(STORE, '$..*').grep(Hash)
    assert_includes titles, { 'title' => 'A', 'price' => 8 }
  end

  def test_missing_member_is_empty_not_an_error
    assert_empty JsonPath::Query.query(STORE, '$.nope.deeper')
    assert_empty JsonPath::Query.query(STORE, '$.store.book[0].nope')
  end

  def test_path_must_start_with_the_root
    error = assert_raises(JsonPath::QueryError) { JsonPath::Query.compile('store.book') }
    assert_match(/must start with \$/, error.message)
  end

  def test_unterminated_bracket_is_rejected
    assert_raises(JsonPath::QueryError) { JsonPath::Query.compile('$.store[') }
  end

  def test_unsupported_bracket_expression_is_rejected
    error = assert_raises(JsonPath::QueryError) { JsonPath::Query.compile('$.book[?(@.price)]') }
    assert_match(/unsupported bracket expression/, error.message)
  end

  def test_empty_dot_name_is_rejected
    assert_raises(JsonPath::QueryError) { JsonPath::Query.compile('$.store..') }
  end
end
