module TomlLite
  alias Value = String | Int64 | Float64 | Bool

  def self.parse_value(raw : String) : Value
    s = raw.strip
    if s.starts_with?("\"") && s.ends_with?("\"") && s.size >= 2
      return s[1, s.size - 2]
    end
    case s
    when "true"  then true
    when "false" then false
    else
      if i = s.to_i64?
        i
      elsif f = s.to_f64?
        f
      else
        s
      end
    end
  end

  def self.parse(text : String) : Hash(String, Value)
    result = Hash(String, Value).new
    table = ""
    text.each_line do |raw|
      line = raw.strip
      next if line.empty?
      next if line.starts_with?("#")
      if line.starts_with?("[") && line.ends_with?("]")
        table = line[1, line.size - 2].strip
        next
      end
      parts = line.split("=", 2)
      next if parts.size < 2
      key = parts[0].strip
      value = parse_value(parts[1].strip)
      full_key = table.empty? ? key : "#{table}.#{key}"
      result[full_key] = value
    end
    result
  end

  def self.render(parsed : Hash(String, Value)) : String
    parsed.keys.sort.map { |k| "#{k} = #{parsed[k]}" }.join("\n")
  end
end
