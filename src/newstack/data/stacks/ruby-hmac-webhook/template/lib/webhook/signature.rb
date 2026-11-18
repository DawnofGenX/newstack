# frozen_string_literal: true

require 'openssl'

module Webhook
  # Stripe-style signatures: HMAC-SHA256 over "<timestamp>.<payload>".
  #
  # The timestamp travels with the signature so a captured header cannot be
  # replayed forever; `verify` is the only place that decides freshness, which
  # keeps the HTTP layer free of clock policy.
  module Signature
    SCHEME = 'v1'
    DEFAULT_TOLERANCE = 300

    module_function

    def sign(secret:, payload:, timestamp:)
      "t=#{timestamp},#{SCHEME}=#{digest(secret, timestamp, payload)}"
    end

    # Returns :ok, :expired or :invalid. Never raises on a malformed header.
    def verify(header:, secret:, payload:, now:, tolerance: DEFAULT_TOLERANCE)
      fields = parse(header)
      return :invalid if fields.nil?

      timestamp = fields[:timestamp]
      return :expired if (now - timestamp).abs > tolerance
      return :invalid unless secure_compare(fields[:signature], digest(secret, timestamp, payload))

      :ok
    end

    def digest(secret, timestamp, payload)
      OpenSSL::HMAC.hexdigest('SHA256', secret.to_s, "#{timestamp}.#{payload}")
    end

    def parse(header)
      pairs = header.to_s.split(',').map { |part| part.split('=', 2) }
      return nil unless pairs.all? { |pair| pair.length == 2 }

      fields = pairs.to_h
      raw_timestamp = fields['t']
      signature = fields[SCHEME]
      return nil if raw_timestamp.nil? || signature.nil? || signature.empty?
      return nil unless raw_timestamp.match?(/\A\d+\z/)

      { timestamp: Integer(raw_timestamp, 10), signature: signature }
    end

    def secure_compare(left, right)
      return false unless left.bytesize == right.bytesize

      OpenSSL.fixed_length_secure_compare(left, right)
    end
  end
end
