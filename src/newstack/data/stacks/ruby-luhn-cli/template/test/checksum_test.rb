# frozen_string_literal: true

require_relative 'test_helper'

class ChecksumTest < Minitest::Test
  def test_valid_known_card
    assert Luhn::Checksum.valid?('4111 1111 1111 1111')
    assert Luhn::Checksum.valid?('5500000000000004')
  end

  def test_invalid
    refute Luhn::Checksum.valid?('4111 1111 1111 1112')
  end

  def test_check_digit
    assert_equal 1, Luhn::Checksum.check_digit('411111111111111')
  end

  def test_generate
    assert_equal '4111111111111111', Luhn::Checksum.generate('411111111111111')
  end

  def test_brand
    assert_equal 'visa', Luhn::Checksum.brand('4111111111111111')
    assert_equal 'mastercard', Luhn::Checksum.brand('5500000000000004')
    assert_equal 'amex', Luhn::Checksum.brand('378282246310005')
    assert_equal 'unknown', Luhn::Checksum.brand('1234567890123456')
  end
end
