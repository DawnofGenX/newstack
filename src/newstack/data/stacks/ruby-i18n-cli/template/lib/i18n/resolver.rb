# frozen_string_literal: true

require 'yaml'

module I18n
  class Resolver
    attr_reader :locales_dir, :default_locale

    def initialize(locales_dir, default_locale: 'en')
      @locales_dir = locales_dir
      @default_locale = default_locale
      @cache = {}
    end

    def fallback_chain(locale)
      parts = locale.to_s.split('-')
      chain = []
      parts.size.downto(1) do |n|
        chain << parts.first(n).join('-')
      end
      chain << @default_locale unless chain.include?(@default_locale)
      chain.uniq
    end

    def load(locale)
      return @cache[locale] if @cache.key?(locale)

      path = locale_path(locale)
      data = File.exist?(path) ? (YAML.load_file(path) || {}) : {}
      data = data[locale] if data.is_a?(Hash) && data.size == 1 && data.key?(locale)
      @cache[locale] = data.is_a?(Hash) ? data : {}
      @cache[locale]
    end

    def resolve(key, locale:)
      fallback_chain(locale).each do |loc|
        data = load(loc)
        return dig(data, key) if has_path?(data, key)
      end
      nil
    end

    def missing?(key, locale:)
      !has_path_in_chain?(key, locale)
    end

    def check(target_locale)
      en_keys = flatten_keys(load(@default_locale))
      target_keys = flatten_keys(load(target_locale))
      en_keys - target_keys
    end

    def all_keys(locale = @default_locale)
      flatten_keys(load(locale))
    end

    private

    def locale_path(locale)
      %w[yml yaml].each do |ext|
        candidate = File.join(@locales_dir, "#{locale}.#{ext}")
        return candidate if File.exist?(candidate)
      end
      File.join(@locales_dir, "#{locale}.yml")
    end

    def has_path?(data, key)
      return false unless data.is_a?(Hash)

      key.split('.').reduce(data) do |acc, part|
        return false unless acc.is_a?(Hash) && (acc.key?(part) || acc.key?(part.to_sym))

        acc.key?(part) ? acc[part] : acc[part.to_sym]
      end
      true
    rescue StandardError
      false
    end

    def has_path_in_chain?(key, locale)
      fallback_chain(locale).any? { |loc| has_path?(load(loc), key) }
    end

    def dig(data, key)
      key.split('.').reduce(data) do |acc, part|
        return nil unless acc.is_a?(Hash)

        acc.key?(part) ? acc[part] : acc[part.to_sym]
      end
    end

    def flatten_keys(hash, prefix = '')
      return [] unless hash.is_a?(Hash)

      hash.flat_map do |k, v|
        path = prefix.empty? ? k.to_s : "#{prefix}.#{k}"
        if v.is_a?(Hash)
          flatten_keys(v, path)
        else
          [path]
        end
      end
    end
  end
end
