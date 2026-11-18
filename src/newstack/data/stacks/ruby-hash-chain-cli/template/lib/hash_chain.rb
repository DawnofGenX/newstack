# frozen_string_literal: true

require 'digest'
require 'json'

# An append-only hash chain: every entry commits to the digest of the one before
# it, so editing, inserting, reordering or truncating history is detectable
# without trusting whoever stored the file.
module HashChain
  # The digest a chain starts from: sixty-four zeroes, the width of a sha256.
  GENESIS = ('0' * 64).freeze

  Entry = Data.define(:seq, :at, :payload, :prev, :digest)

  # Raised when a chain fails verification. `index` is the 0-based position of
  # the first bad entry, or nil when the failure is structural (empty file).
  class Broken < StandardError
    attr_reader :index, :reason

    def initialize(reason, index = nil)
      @reason = reason
      @index = index
      super(index ? "entry #{index}: #{reason}" : reason)
    end
  end

  module_function

  # JSON with sorted keys and no insignificant whitespace, so two callers that
  # build the same object in a different order agree on the digest. Values keep
  # their JSON types; a Hash payload never collapses to an inspected string.
  def canonical(payload)
    JSON.generate(sort_keys(payload))
  end

  def sort_keys(value)
    case value
    when Hash then value.keys.sort.each_with_object({}) { |key, out| out[key] = sort_keys(value[key]) }
    when Array then value.map { |item| sort_keys(item) }
    else value
    end
  end

  # sha256 over the fields that must not change: the sequence number, the
  # timestamp, the previous digest and the canonical payload. Line-oriented so
  # that a field cannot be smuggled into its neighbour.
  def link(prev, payload, seq:, at:)
    Digest::SHA256.hexdigest([seq.to_s, at.to_s, prev, canonical(payload)].join("\n"))
  end

  def hex?(text)
    text.is_a?(String) && text.match?(/\A[0-9a-f]{64}\z/)
  end

  # In-memory chain. Append is the only mutation; entries are frozen values.
  class Chain
    attr_reader :entries

    def initialize(entries = [])
      @entries = entries.freeze
    end

    def empty?
      entries.empty?
    end

    def length
      entries.length
    end

    def head
      entries.empty? ? HashChain::GENESIS : entries.last.digest
    end

    def append(payload, at: Time.now.to_i)
      seq = entries.length
      prev = head
      digest = HashChain.link(prev, payload, seq: seq, at: at)
      @entries = (entries + [HashChain::Entry.new(seq: seq, at: at, payload: payload, prev: prev, digest: digest)]).freeze
      entries.last
    end

    # Raises HashChain::Broken at the first entry that does not match its own
    # digest or does not chain onto its predecessor. Returns self when clean.
    def verify!
      expected_prev = HashChain::GENESIS
      entries.each_with_index do |entry, index|
        raise HashChain::Broken.new("sequence is #{entry.seq}, expected #{index}", index) unless entry.seq == index
        raise HashChain::Broken.new("prev is #{entry.prev[0, 12]}..., expected #{expected_prev[0, 12]}...", index) unless entry.prev == expected_prev

        recomputed = HashChain.link(expected_prev, entry.payload, seq: entry.seq, at: entry.at)
        raise HashChain::Broken.new("digest does not match contents", index) unless recomputed == entry.digest

        expected_prev = entry.digest
      end
      self
    end

    def verify
      verify!
      [true, nil]
    rescue HashChain::Broken => e
      [false, e]
    end

    # One JSON object per line, in chain order.
    def to_ndjson
      entries.map do |entry|
        JSON.generate({ 'seq' => entry.seq, 'at' => entry.at, 'payload' => entry.payload,
                        'prev' => entry.prev, 'digest' => entry.digest })
      end.join("\n") + (entries.empty? ? '' : "\n")
    end

    def self.parse(text)
      entries = text.each_line.filter_map do |line|
        line = line.strip
        next if line.empty?

        object = JSON.parse(line)
        Entry.new(seq: Integer(object.fetch('seq')), at: Integer(object.fetch('at')),
                  payload: object.fetch('payload'), prev: object.fetch('prev'),
                  digest: object.fetch('digest'))
      end
      new(entries)
    end
  end
end
