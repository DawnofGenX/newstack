# frozen_string_literal: true

require 'test_helper'

class HashChainTest < Minitest::Test
  def test_canonical_sorts_keys_so_order_does_not_matter
    assert_equal '{"a":1,"b":2}', HashChain.canonical({ 'b' => 2, 'a' => 1 })
    assert_equal HashChain.canonical({ 'a' => 1, 'b' => { 'd' => 4, 'c' => 3 } }),
                 HashChain.canonical({ 'b' => { 'c' => 3, 'd' => 4 }, 'a' => 1 })
  end

  def test_canonical_keeps_json_types
    assert_equal '{"n":1,"s":"1"}', HashChain.canonical({ 'n' => 1, 's' => '1' })
  end

  def test_genesis_is_the_link_of_the_first_entry
    digest = HashChain.link(HashChain::GENESIS, { 'a' => 1 }, seq: 0, at: 100)
    assert_match(/\A[0-9a-f]{64}\z/, digest)
    assert_equal digest, HashChain.link(HashChain::GENESIS, { 'a' => 1 }, seq: 0, at: 100)
  end

  def test_any_field_change_changes_the_digest
    base = HashChain.link(HashChain::GENESIS, { 'a' => 1 }, seq: 0, at: 100)
    refute_equal base, HashChain.link(HashChain::GENESIS, { 'a' => 2 }, seq: 0, at: 100)
    refute_equal base, HashChain.link(HashChain::GENESIS, { 'a' => 1 }, seq: 1, at: 100)
    refute_equal base, HashChain.link(HashChain::GENESIS, { 'a' => 1 }, seq: 0, at: 101)
    refute_equal base, HashChain.link('1' * 64, { 'a' => 1 }, seq: 0, at: 100)
  end

  def test_append_chains_entries_and_verify_accepts_them
    chain = HashChain::Chain.new
    first = chain.append({ 'event' => 'created' }, at: 100)
    second = chain.append({ 'event' => 'paid' }, at: 200)

    assert_equal HashChain::GENESIS, first.prev
    assert_equal first.digest, second.prev
    assert_equal [0, 1], chain.entries.map(&:seq)
    assert_equal second.digest, chain.head
    assert_same chain, chain.verify!
  end

  def test_editing_a_payload_is_detected
    chain = HashChain::Chain.new
    chain.append({ 'amount' => 10 }, at: 100)
    chain.append({ 'amount' => 20 }, at: 200)
    tampered = HashChain::Chain.new([chain.entries[0], chain.entries[1].with(payload: { 'amount' => 99 })])
    ok, error = tampered.verify
    refute ok
    assert_equal 1, error.index
    assert_equal 'digest does not match contents', error.reason
  end

  def test_dropping_an_entry_is_detected
    chain = HashChain::Chain.new
    chain.append({ 'n' => 1 }, at: 1)
    chain.append({ 'n' => 2 }, at: 2)
    chain.append({ 'n' => 3 }, at: 3)
    truncated = HashChain::Chain.new([chain.entries[0], chain.entries[2]])
    ok, error = truncated.verify
    refute ok
    assert_equal 1, error.index
    assert_match(/sequence is 2, expected 1/, error.reason)
  end

  def test_reordering_is_detected
    chain = HashChain::Chain.new
    chain.append({ 'n' => 1 }, at: 1)
    chain.append({ 'n' => 2 }, at: 2)
    swapped = HashChain::Chain.new([chain.entries[1], chain.entries[0]])
    refute swapped.verify.first
  end

  def test_round_trips_through_ndjson
    chain = HashChain::Chain.new
    chain.append({ 'a' => [1, 2] }, at: 10)
    chain.append({ 'b' => 'x' }, at: 11)
    restored = HashChain::Chain.parse(chain.to_ndjson)
    assert_equal chain.length, restored.length
    assert_equal chain.head, restored.head
    assert restored.verify.first
  end

  def test_empty_chain_has_the_genesis_head
    chain = HashChain::Chain.new
    assert chain.empty?
    assert_equal HashChain::GENESIS, chain.head
    assert chain.verify.first
  end
end
