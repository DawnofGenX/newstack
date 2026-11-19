# frozen_string_literal: true

require 'json'

module JsonDiff
  class Error < StandardError; end

  Change = Struct.new(:path, :kind, :left, :right, keyword_init: true) do
    def to_s
      case kind
      when :changed then "#{path}: #{left.inspect} -> #{right.inspect}"
      when :added   then "#{path}: + #{right.inspect}"
      when :removed then "#{path}: - #{left.inspect}"
      end
    end
  end

  module_function

  def parse(text)
    JSON.parse(text)
  rescue JSON::ParserError => e
    raise Error, "invalid JSON: #{e.message}"
  end

  def diff(left, right, path = '')
    left = safe_parse(left)
    right = safe_parse(right)
    diff_values(left, right, path)
  end

  def safe_parse(value)
    return value unless value.is_a?(String)
    JSON.parse(value)
  rescue JSON::ParserError
    value
  end

  def diff_values(left, right, path)
    changes = []
    if left.is_a?(Hash) && right.is_a?(Hash)
      (left.keys | right.keys).sort.each do |key|
        sub = path.empty? ? key.to_s : "#{path}.#{key}"
        if left.key?(key) && right.key?(key)
          changes.concat(diff_values(left[key], right[key], sub))
        elsif left.key?(key)
          changes << Change.new(path: sub, kind: :removed, left: left[key])
        else
          changes << Change.new(path: sub, kind: :added, right: right[key])
        end
      end
    elsif left.is_a?(Array) && right.is_a?(Array)
      n = [left.length, right.length].max
      n.times do |i|
        sub = "#{path}[#{i}]"
        if i < left.length && i < right.length
          changes.concat(diff_values(left[i], right[i], sub))
        elsif i < left.length
          changes << Change.new(path: sub, kind: :removed, left: left[i])
        else
          changes << Change.new(path: sub, kind: :added, right: right[i])
        end
      end
    else
      unless left == right
        changes << Change.new(path: path.empty? ? '(root)' : path, kind: :changed, left: left, right: right)
      end
    end
    changes
  end
end