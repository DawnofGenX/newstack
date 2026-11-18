# frozen_string_literal: true

# Huffman coding: build a prefix code from text, dump it with the bits, decode it back.
module Huffman
  # A node of the Huffman tree: a leaf carries a symbol, a branch carries two.
  class Node
    attr_reader :weight, :symbol, :left, :right

    def initialize(weight, symbol: nil, left: nil, right: nil)
      @weight = weight
      @symbol = symbol
      @left = left
      @right = right
    end

    def leaf?
      @left.nil? && @right.nil?
    end
  end

  # Raised when a payload or a bit string cannot be decoded.
  class DecodeError < StandardError; end

  module_function

  def frequencies(text)
    counts = Hash.new(0)
    text.each_char { |char| counts[char] += 1 }
    counts
  end

  # Builds the tree by repeatedly merging the two lightest nodes.
  def build(frequencies)
    nodes = frequencies.map { |symbol, weight| Node.new(weight, symbol: symbol) }
    nodes.sort_by! { |node| [node.weight, node.symbol.to_s] }
    while nodes.length > 1
      left = nodes.shift
      right = nodes.shift
      merged = Node.new(left.weight + right.weight, left: left, right: right)
      index = nodes.bsearch_index { |node| node.weight > merged.weight } || nodes.length
      nodes.insert(index, merged)
    end
    nodes.first
  end

  def tree_for(text)
    counts = frequencies(text)
    counts.empty? ? nil : build(counts)
  end

  # Code table from the tree: walking left appends 0, right appends 1.
  def codes(tree)
    return {} if tree.nil?

    table = {}
    walk = lambda do |node, prefix|
      if node.leaf?
        table[node.symbol] = prefix.empty? ? '0' : prefix
        next
      end
      walk.call(node.left, "#{prefix}0")
      walk.call(node.right, "#{prefix}1")
    end
    walk.call(tree, '')
    table
  end

  def encode(text, table = nil)
    table ||= codes(tree_for(text))
    text.each_char.map { |char| table.fetch(char) }.join
  end

  # Decodes with a code table (the inverse map), not the tree.
  def decode(bits, table)
    return '' if bits.empty? && table.empty?

    inverse = table.invert
    raise DecodeError, 'cannot decode with an empty code table' if inverse.empty?

    longest = inverse.keys.map(&:length).max
    out = +''
    buffer = +''
    bits.each_char.with_index do |bit, index|
      unless %w[0 1].include?(bit)
        raise DecodeError, "invalid bit #{bit.inspect} at offset #{index}"
      end
      buffer << bit
      if (symbol = inverse[buffer])
        out << symbol
        buffer = +''
      elsif buffer.length > longest
        raise DecodeError, "no code matches #{buffer.inspect} at offset #{index}"
      end
    end
    raise DecodeError, 'bit string ends in the middle of a code' unless buffer.empty?

    out
  end

  # A self-describing payload: the entry count, one `code inspect(symbol)` line
  # per entry, then the bits. Decoding needs nothing but this text.
  def dump(text)
    table = codes(tree_for(text))
    lines = [table.length.to_s]
    table.each { |symbol, code| lines << "#{code} #{symbol.inspect}" }
    lines << encode(text, table)
    lines.join("\n")
  end

  def load(payload)
    lines = payload.split("\n")
    raise DecodeError, 'empty payload' if lines.empty?

    count = Integer(lines.shift, exception: false)
    raise DecodeError, "expected an entry count, got #{lines.first.inspect}" if count.nil?

    table = {}
    count.times do
      line = lines.shift
      raise DecodeError, "expected #{count} table entries, got #{table.length}" if line.nil?

      code, literal = line.split(' ', 2)
      raise DecodeError, "malformed table entry #{line.inspect}" if code.nil? || literal.nil?

      symbol = literal.undump
      raise DecodeError, "duplicate table entry for #{literal}" if table.key?(symbol)

      table[symbol] = code
    end
    bits = lines.join
    [bits, table]
  end

  # Packs a bit string into bytes, padding the final byte with zeros.
  def pack(bits)
    bytes = bits.chars.each_slice(8).map { |slice| slice.join.ljust(8, '0').to_i(2) }
    bytes.pack('C*')
  end

  def compressed_bytes(text)
    (encode(text).length / 8.0).ceil
  end
end
