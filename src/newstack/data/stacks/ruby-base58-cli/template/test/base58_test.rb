# frozen_string_literal: true

require 'minitest/autorun'

require_relative '../lib/base58'

class Base58Test < Minitest::Test
  def hex(text)
    [text].pack('H*')
  end

  def test_empty_input_encodes_to_an_empty_string
    assert_equal '', Base58.encode(''.b)
  end

  def test_single_byte_uses_two_characters
    assert_equal '2g', Base58.encode(hex('61'))
  end

  def test_repeated_bytes_match_the_reference_vectors
    assert_equal 'a3gV', Base58.encode(hex('626262'))
    assert_equal 'aPEr', Base58.encode(hex('636363'))
  end

  def test_a_sentence_round_trips_through_the_reference_vector
    assert_equal 'StV1DL6CwTryKyV', Base58.encode('hello world'.b)
    assert_equal '73696d706c792061206c6f6e6720737472696e67',
                 Base58.decode('2cFupjhnEsSn59qHXstmK2ffpLv2').unpack1('H*')
  end

  def test_leading_zero_bytes_become_leading_ones
    assert_equal '112', Base58.encode(hex('000001'))
    assert_equal '000001', Base58.decode('112').unpack1('H*')
  end

  def test_every_leading_zero_survives_a_round_trip
    payload = hex('0000000000000001ff')
    assert_equal payload, Base58.decode(Base58.encode(payload))
  end

  def test_lookalike_characters_are_refused
    error = assert_raises(Base58::Error) { Base58.decode('2g0') }
    assert_includes error.message, 'invalid base58 character: "0"'
  end

  def test_an_empty_string_is_not_a_value
    assert_raises(Base58::Error) { Base58.decode('') }
  end

  def test_check_encoding_appends_a_four_byte_checksum
    payload = hex('000f9a4b120000000000')
    encoded = Base58.encode_check(payload)
    assert_equal '12JNo32w2yrmQuWFckG', encoded
    assert_equal payload, Base58.decode_check(encoded)
  end

  def test_a_single_changed_character_fails_the_checksum
    encoded = Base58.encode_check('hello world'.b)
    tampered = encoded.dup
    tampered[-1] = tampered[-1] == '2' ? '3' : '2'
    error = assert_raises(Base58::Error) { Base58.decode_check(tampered) }
    assert_includes error.message, 'checksum mismatch'
  end

  def test_a_value_shorter_than_the_checksum_is_refused
    assert_raises(Base58::Error) { Base58.decode_check('2g') }
  end

  def test_round_trip_of_a_longer_payload
    payload = (0..32).to_a.pack('C*')
    assert_equal payload, Base58.decode(Base58.encode(payload))
    assert_equal payload, Base58.decode_check(Base58.encode_check(payload))
  end
end
