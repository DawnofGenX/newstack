# frozen_string_literal: true

require_relative 'test_helper'

class SignatureTest < Minitest::Test
  SECRET = 'whsec_test'
  PAYLOAD = '{"id":1}'
  TIMESTAMP = 1_700_000_000
  # HMAC-SHA256 over the string 1700000000.{"id":1}, pinned from a reference
  # run so a change to the signed string breaks this test instead of receivers.
  DIGEST = '2f441ba4b3b2d50d28a9ab9d9fd8880376ecd1eb5d0435401553f5d8d0a5dcf8'

  def header(overrides = {})
    values = { timestamp: TIMESTAMP, digest: DIGEST }.merge(overrides)
    "t=#{values[:timestamp]},v1=#{values[:digest]}"
  end

  def verify(header_value, payload: PAYLOAD, now: TIMESTAMP, tolerance: 300)
    Webhook::Signature.verify(
      header: header_value,
      secret: SECRET,
      payload: payload,
      now: now,
      tolerance: tolerance
    )
  end

  def test_sign_matches_the_pinned_vector
    assert_equal "t=#{TIMESTAMP},v1=#{DIGEST}",
                 Webhook::Signature.sign(secret: SECRET, payload: PAYLOAD, timestamp: TIMESTAMP)
  end

  def test_a_fresh_matching_header_is_accepted
    assert_equal :ok, verify(header)
  end

  def test_the_tolerance_window_is_inclusive_at_its_edge
    assert_equal :ok, verify(header, now: TIMESTAMP + 300)
    assert_equal :expired, verify(header, now: TIMESTAMP + 301)
  end

  def test_a_stale_header_is_expired_not_invalid
    assert_equal :expired, verify(header, now: TIMESTAMP + 10_000)
  end

  def test_a_wrong_secret_is_invalid
    result = Webhook::Signature.verify(
      header: header, secret: 'whsec_other', payload: PAYLOAD, now: TIMESTAMP
    )
    assert_equal :invalid, result
  end

  def test_a_tampered_payload_is_invalid
    assert_equal :invalid, verify(header, payload: '{"id":2}')
  end

  def test_a_signature_of_the_wrong_length_is_invalid_not_an_exception
    assert_equal :invalid, verify(header(digest: 'abc'))
  end

  def test_a_header_without_a_timestamp_is_invalid
    assert_equal :invalid, verify("v1=#{DIGEST}")
  end

  def test_a_header_without_a_signature_is_invalid
    assert_equal :invalid, verify("t=#{TIMESTAMP}")
  end

  def test_a_non_numeric_timestamp_is_invalid
    assert_equal :invalid, verify("t=yesterday,v1=#{DIGEST}")
  end

  def test_a_header_of_garbage_is_invalid
    assert_equal :invalid, verify('nonsense')
  end

  def test_a_unicode_payload_round_trips
    payload = 'héllo wörld'
    signed = Webhook::Signature.sign(secret: SECRET, payload: payload, timestamp: TIMESTAMP)
    assert_equal :ok, verify(signed, payload: payload)
  end
end
