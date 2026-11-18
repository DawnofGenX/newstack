# frozen_string_literal: true

require 'test_helper'
require 'tmpdir'
require 'fileutils'

class ResolverTest < Minitest::Test
  def setup
    @dir = Dir.mktmpdir
    File.write(File.join(@dir, 'en.yml'), <<~YAML)
      en:
        greeting: Hello
        user:
          name: Name
        farewell: Bye
    YAML
    File.write(File.join(@dir, 'de.yml'), <<~YAML)
      de:
        greeting: Hallo
    YAML
    File.write(File.join(@dir, 'de-AT.yml'), <<~YAML)
      de-AT:
        greeting: Servus
    YAML
  end

  def teardown
    FileUtils.rm_rf(@dir)
  end

  def test_fallback_chain
    r = I18n::Resolver.new(@dir)
    assert_equal %w[de-AT de en], r.fallback_chain('de-AT')
  end

  def test_resolve_with_fallback
    r = I18n::Resolver.new(@dir)
    assert_equal 'Servus', r.resolve('greeting', locale: 'de-AT')
    assert_equal 'Hallo', r.resolve('greeting', locale: 'de')
    assert_equal 'Hello', r.resolve('greeting', locale: 'fr')
  end

  def test_nested_key
    r = I18n::Resolver.new(@dir)
    assert_equal 'Name', r.resolve('user.name', locale: 'en')
    assert_equal 'Name', r.resolve('user.name', locale: 'de') # fallback to en
  end

  def test_missing_key
    r = I18n::Resolver.new(@dir)
    assert_nil r.resolve('nope', locale: 'de')
    assert r.missing?('nope', locale: 'de')
  end

  def test_check_missing
    r = I18n::Resolver.new(@dir)
    missing = r.check('de')
    assert_includes missing, 'user.name'
    assert_includes missing, 'farewell'
    refute_includes missing, 'greeting'
  end
end
