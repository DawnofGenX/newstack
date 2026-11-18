# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../lib/huffman'

class HuffmanTest < Minitest::Test
  def test_frequencies_counts_characters
    assert_equal({ 'a' => 2, 'b' => 1 }, Huffman.frequencies('aba'))
  end

  def test_the_tree_root_weighs_the_whole_input
    tree = Huffman.tree_for('abracadabra')
    assert_equal 11, tree.weight
    refute tree.leaf?
  end

  def test_codes_are_prefix_free
    table = Huffman.codes(Huffman.tree_for('abracadabra'))
    codes = table.values
    codes.each do |code|
      codes.each do |other|
        next if other.equal?(code)

        refute other.start_with?(code), "#{code} is a prefix of #{other}"
      end
    end
  end

  def test_the_most_frequent_symbol_gets_the_shortest_code
    table = Huffman.codes(Huffman.tree_for('aaaabbc'))
    assert_operator table['a'].length, :<=, table['c'].length
  end

  def test_encode_and_decode_round_trip
    text = 'the quick brown fox jumps over the lazy dog'
    bits = Huffman.encode(text)
    assert_equal text, Huffman.decode(bits, Huffman.codes(Huffman.tree_for(text)))
  end

  def test_a_single_symbol_uses_one_bit
    table = Huffman.codes(Huffman.tree_for('aaaa'))
    assert_equal({ 'a' => '0' }, table)
    assert_equal '0000', Huffman.encode('aaaa', table)
    assert_equal 'aaaa', Huffman.decode('0000', table)
  end

  def test_dump_and_load_round_trip
    text = "a\tb\nc a b a"
    payload = Huffman.dump(text)
    bits, table = Huffman.load(payload)
    assert_equal text, Huffman.decode(bits, table)
  end

  def test_an_empty_document_round_trips
    assert_equal '', Huffman.decode(*Huffman.load(Huffman.dump('')).reverse)
  end

  def test_decode_rejects_a_bad_bit
    table = Huffman.codes(Huffman.tree_for('ab'))
    error = assert_raises(Huffman::DecodeError) { Huffman.decode('0x1', table) }
    assert_match(/invalid bit/, error.message)
  end

  def test_decode_rejects_a_truncated_code
    error = assert_raises(Huffman::DecodeError) { Huffman.decode('1', 'a' => '0', 'b' => '10') }
    assert_match(/ends in the middle/, error.message)
  end

  def test_load_rejects_a_malformed_payload
    assert_raises(Huffman::DecodeError) { Huffman.load('nope') }
    assert_raises(Huffman::DecodeError) { Huffman.load("2\n0 \"a\"") }
  end

  def test_pack_pads_the_last_byte
    assert_equal "\xA0".b, Huffman.pack('101')
    assert_equal "\xFF".b, Huffman.pack('11111111')
  end

  def test_compression_shrinks_skewed_text
    text = 'a' * 200 + 'bcdefgh'
    assert_operator Huffman.compressed_bytes(text), :<, text.bytesize
  end
end
