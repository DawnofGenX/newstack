# frozen_string_literal: true

require 'digest'

# Base58 and Base58Check, as used by Bitcoin-style addresses.
#
# The alphabet drops the characters that look alike in print (0, O, I, l) so a
# value can be read aloud or copied by hand without ambiguity. That is the whole
# reason the encoding exists; the arithmetic is otherwise an ordinary base
# conversion done on a big integer.
module Base58
  ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
  INDEX = ALPHABET.each_char.with_index.to_h.freeze

  # Raised for anything the user could have typed wrong: a character outside the
  # alphabet, an empty string, or a payload whose checksum does not match.
  class Error < StandardError; end

  module_function

  # Encodes bytes. Every leading zero byte becomes a leading '1', which is how
  # the encoding stays reversible: the number itself carries no leading zeros.
  def encode(bytes)
    return '' if bytes.empty?

    zeros = 0
    zeros += 1 while zeros < bytes.bytesize && bytes.getbyte(zeros).zero?

    number = bytes.unpack1('H*').to_i(16)
    digits = +''
    while number.positive?
      number, remainder = number.divmod(58)
      digits.prepend(ALPHABET[remainder])
    end
    digits.prepend('1' * zeros)
  end

  # Decodes text back to bytes, rejecting any character that is not in the
  # alphabet — '0OIl' are the usual mistakes.
  def decode(text)
    raise Error, 'empty string is not a base58 value' if text.empty?

    number = 0
    text.each_char do |char|
      index = INDEX[char]
      raise Error, "invalid base58 character: #{char.inspect}" if index.nil?

      number = (number * 58) + index
    end

    zeros = 0
    zeros += 1 while zeros < text.bytesize && text.getbyte(zeros) == 0x31 # '1'

    body = +''
    unless number.zero?
      hex = number.to_s(16)
      hex = "0#{hex}" if hex.length.odd?
      body = [hex].pack('H*')
    end
    ("\x00" * zeros).b + body
  end

  # The four check bytes Base58Check appends: the first four bytes of SHA-256
  # applied twice.
  def checksum(payload)
    Digest::SHA256.digest(Digest::SHA256.digest(payload)).byteslice(0, 4)
  end

  # Payload plus checksum, encoded. A single mistyped character changes the
  # checksum, so a decode can refuse it instead of returning plausible bytes.
  def encode_check(payload)
    encode(payload + checksum(payload))
  end

  # Decodes and verifies. Returns the payload without the check bytes.
  def decode_check(text)
    raw = decode(text)
    raise Error, 'value is too short to carry a checksum' if raw.bytesize < 4

    payload = raw.byteslice(0, raw.bytesize - 4)
    expected = checksum(payload)
    actual = raw.byteslice(raw.bytesize - 4, 4)
    raise Error, 'checksum mismatch' unless actual == expected

    payload
  end
end
