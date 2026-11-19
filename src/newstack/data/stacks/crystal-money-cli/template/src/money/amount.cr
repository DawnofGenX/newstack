module Money
  # Raised for anything a user could have typed wrong.
  class ParseError < Exception
  end

  # The currencies this tool knows, with the symbol used by `--symbol`.
  CURRENCIES = {
    "USD" => "$",
    "EUR" => "€",
    "GBP" => "£",
    "INR" => "₹",
    "JPY" => "¥",
    "AUD" => "A$",
    "CAD" => "C$",
    "CHF" => "CHF ",
  }

  # An amount of money held in minor units, so no arithmetic ever touches a
  # Float. Currencies are three upper-case letters.
  struct Amount
    getter minor : Int64
    getter currency : String

    def initialize(@minor : Int64, @currency : String)
      unless CURRENCIES.has_key?(@currency)
        raise ParseError.new("unknown currency '#{@currency}': expected one of #{CURRENCIES.keys.join(", ")}")
      end
    end

    def self.zero(currency : String) : Amount
      new(0_i64, currency)
    end

    # Reads `USD 12.34`, `USD -0.05`, `USD 1,234.5` and `USD 7`.
    def self.parse(text : String) : Amount
      trimmed = text.strip
      raise ParseError.new("empty amount") if trimmed.empty?

      match = trimmed.match(/\A([A-Za-z]{3})[ ]+(-?)([0-9][0-9,]*)(?:\.([0-9]{1,2}))?\z/)
      unless match
        raise ParseError.new("cannot read '#{trimmed}': expected a form like 'USD 12.34'")
      end

      currency = match[1].upcase
      negative = match[2] == "-"
      digits = match[3].delete(',')
      fraction = match[4]? || ""

      cents = fraction.ljust(2, '0').to_i64
      minor = digits.to_i64 * 100 + cents
      minor = -minor if negative
      new(minor, currency)
    end

    def major : Int64
      @minor // 100
    end

    def cents : Int64
      (@minor % 100).abs
    end

    def negative? : Bool
      @minor < 0
    end

    def zero? : Bool
      @minor == 0
    end

    def +(other : Amount) : Amount
      same_currency(other)
      Amount.new(@minor + other.minor, @currency)
    end

    def -(other : Amount) : Amount
      same_currency(other)
      Amount.new(@minor - other.minor, @currency)
    end

    def negate : Amount
      Amount.new(-@minor, @currency)
    end

    def *(factor : Int32 | Int64) : Amount
      Amount.new(@minor * factor.to_i64, @currency)
    end

    def <=>(other : Amount) : Int32
      same_currency(other)
      @minor <=> other.minor
    end

    def ==(other : Amount) : Bool
      @minor == other.minor && @currency == other.currency
    end

    def to_s(io : IO) : Nil
      sign = @minor < 0 ? "-" : ""
      io << @currency << ' ' << sign << (@minor.abs // 100) << '.' << ((@minor.abs % 100).to_s.rjust(2, '0'))
    end

    # `USD 12.34` becomes `$12.34`; unknown symbols fall back to the code.
    def with_symbol : String
      symbol = CURRENCIES[@currency]? || "#{@currency} "
      sign = @minor < 0 ? "-" : ""
      "#{sign}#{symbol}#{@minor.abs // 100}.#{(@minor.abs % 100).to_s.rjust(2, '0')}"
    end

    private def same_currency(other : Amount) : Nil
      return if @currency == other.currency
      raise ParseError.new("cannot mix #{@currency} and #{other.currency}")
    end

    # Splits the amount by ratios, giving leftover minor units to the earliest
    # shares so the parts always add back up to the whole.
    def self.split(amount : Amount, ratios : Array(Int32)) : Array(Amount)
      raise ParseError.new("need at least one ratio") if ratios.empty?
      raise ParseError.new("ratios must not be negative") if ratios.any?(&.<(0))
      total = ratios.sum
      raise ParseError.new("ratios must not all be zero") if total.zero?

      sign = amount.minor < 0 ? -1_i64 : 1_i64
      magnitude = amount.minor.abs
      base = magnitude // total
      leftover = (magnitude % total).to_i64

      shares = ratios.map_with_index do |ratio, index|
        extra = index < leftover ? 1_i64 : 0_i64
        Amount.new(sign * (base * ratio + extra), amount.currency)
      end
      shares
    end
  end
end
