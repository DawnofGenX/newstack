# frozen_string_literal: true

module Luhn
  module Checksum
    module_function

    def clean(number)
      number.to_s.gsub(/[\s-]/, '')
    end

    def digits(number)
      clean(number).chars.map(&:to_i)
    end

    def valid?(number)
      ds = digits(number)
      return false if ds.empty? || ds.any? { |d| d < 0 || d > 9 }
      # Luhn
      sum = 0
      ds.reverse.each_with_index do |d, i|
        if i.odd?
          doubled = d * 2
          doubled -= 9 if doubled > 9
          sum += doubled
        else
          sum += d
        end
      end
      (sum % 10).zero?
    end

    def check_digit(prefix)
      # compute digit that makes prefix+digit valid
      base = clean(prefix)
      raise ArgumentError, 'prefix must be digits' unless base.match?(/\A\d+\z/)
      (0..9).each do |d|
        return d if valid?(base + d.to_s)
      end
      raise 'no check digit found'
    end

    def generate(prefix)
      "#{clean(prefix)}#{check_digit(prefix)}"
    end

    def brand(number)
      n = clean(number)
      return 'visa' if n.match?(/\A4\d{12}(\d{3})?\z/)
      return 'mastercard' if n.match?(/\A5[1-5]\d{14}\z/) || n.match?(/\A2(22[1-9]|2[3-9]|[3-6]|7[01]|720)\d{12}\z/)
      return 'amex' if n.match?(/\A3[47]\d{13}\z/)
      return 'discover' if n.match?(/\A6(?:011|5)\d{12,15}\z/)
      'unknown'
    end
  end
end
