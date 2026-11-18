# frozen_string_literal: true

module JsonPath
  # Raised for a path that cannot be parsed; the CLI turns it into a usage error.
  class QueryError < StandardError; end

  # A compiled path is a list of steps. Each step keeps the parsed form so evaluation never
  # re-parses the path for every node it visits.
  Step = Struct.new(:kind, :value)

  # A small, dependency-free JSONPath subset:
  #
  #   $                  the root value
  #   .name  ['name']    an object member
  #   [0]    [-1]        an array element, negative counts from the end
  #   .*     [*]         every member or element
  #   ..name             name at any depth
  #   ..*                every value at any depth
  module Query
    module_function

    # Compiles `path` into steps, raising QueryError for anything outside the subset.
    def compile(path)
      raise QueryError, 'path must be a non-empty string' if path.nil? || path.empty?
      raise QueryError, "path must start with $: #{path.inspect}" unless path.start_with?('$')

      steps = []
      index = 1
      while index < path.length
        char = path[index]
        case char
        when '.'
          if path[index + 1] == '.'
            step, index = descend_step(path, index + 2)
          else
            step, index = child_step(path, index + 1)
          end
          steps << step
        when '['
          close = path.index(']', index)
          raise QueryError, "unterminated [ in #{path.inspect}" if close.nil?

          steps << bracket_step(path[(index + 1)...close], path)
          index = close + 1
        else
          raise QueryError, "unexpected #{char.inspect} at #{index} in #{path.inspect}"
        end
      end
      steps
    end

    # Every value `path` selects from `data`, in document order.
    def query(data, path)
      steps = path.is_a?(Array) ? path : compile(path)
      steps.reduce([data]) { |nodes, step| nodes.flat_map { |node| apply(node, step) } }
    end

    def apply(node, step)
      case step.kind
      when :key then node.is_a?(Hash) && node.key?(step.value) ? [node[step.value]] : []
      when :index then index_match(node, step.value)
      when :wildcard then wildcard(node)
      when :descend_key then descend_key(node, step.value)
      when :descend_wildcard then descend_wildcard(node)
      else raise QueryError, "unknown step #{step.kind.inspect}"
      end
    end

    def index_match(node, index)
      return [] unless node.is_a?(Array)

      position = index.negative? ? node.length + index : index
      position.negative? || position >= node.length ? [] : [node[position]]
    end

    def wildcard(node)
      case node
      when Hash then node.values
      when Array then node
      else []
      end
    end

    def descend_key(node, key)
      matches = []
      each_node(node) do |candidate|
        matches << candidate[key] if candidate.is_a?(Hash) && candidate.key?(key)
      end
      matches
    end

    def descend_wildcard(node)
      matches = []
      each_node(node, include_self: false) { |candidate| matches << candidate }
      matches
    end

    # Depth first walk over hashes and arrays, yielding each node.
    def each_node(node, include_self: true, &block)
      block.call(node) if include_self
      case node
      when Hash then node.each_value { |value| each_node(value, &block) }
      when Array then node.each { |value| each_node(value, &block) }
      end
    end

    def child_step(path, index)
      return [Step.new(:wildcard, nil), index + 1] if path[index] == '*'

      name, cursor = read_name(path, index)
      [Step.new(:key, name), cursor]
    end

    def descend_step(path, index)
      return [Step.new(:descend_wildcard, nil), index + 1] if path[index] == '*'

      name, cursor = read_name(path, index)
      [Step.new(:descend_key, name), cursor]
    end

    def read_name(path, index)
      start = index
      index += 1 while index < path.length && path[index] != '.' && path[index] != '['
      name = path[start...index]
      raise QueryError, "empty name at #{start} in #{path.inspect}" if name.empty?

      [name, index]
    end

    def bracket_step(inner, path)
      text = inner.strip
      raise QueryError, "empty [] in #{path.inspect}" if text.empty?
      return Step.new(:wildcard, nil) if text == '*'

      quoted = text.match(/\A(['"])(.*)\1\z/m)
      return Step.new(:key, quoted[2]) if quoted

      number = text.match(/\A(-?\d+)\z/)
      return Step.new(:index, number[1].to_i) if number

      raise QueryError, "unsupported bracket expression [#{inner}] in #{path.inspect}"
    end
  end
end
