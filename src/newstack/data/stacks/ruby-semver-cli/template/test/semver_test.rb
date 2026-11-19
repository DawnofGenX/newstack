# frozen_string_literal: true

require 'minitest/autorun'

require_relative '../lib/semver'

class SemverTest < Minitest::Test
  def test_parse_basic
    v = Semver.parse('1.2.3')
    assert_equal 1, v.major
    assert_equal 2, v.minor
    assert_equal 3, v.patch
    assert_nil v.pre
  end

  def test_parse_pre_release
    v = Semver.parse('1.2.3-rc.1')
    assert_equal 'rc.1', v.pre
  end

  def test_parse_build_metadata
    v = Semver.parse('1.2.3+build.42')
    assert_equal 'build.42', v.build
  end

  def test_valid
    assert Semver.valid?('1.2.3')
    assert Semver.valid?('1.2.3-rc.1+build')
    refute Semver.valid?('1.2')
    refute Semver.valid?('a.b.c')
  end

  def test_compare_precedence_table
    pairs = [
      ['1.0.0', '2.0.0', -1],
      ['1.0.0', '1.1.0', -1],
      ['1.0.0', '1.0.1', -1],
      ['1.0.0-alpha', '1.0.0', -1],
      ['1.0.0-alpha', '1.0.0-alpha.1', -1],
      ['1.0.0-alpha.1', '1.0.0-alpha.beta', -1],
      ['1.0.0-alpha.beta', '1.0.0-beta', -1],
      ['1.0.0-beta', '1.0.0-beta.2', -1],
      ['1.0.0-beta.2', '1.0.0-beta.11', -1],
      ['1.0.0-beta.11', '1.0.0-rc.1', -1],
      ['1.0.0-rc.1', '1.0.0', -1],
      ['1.0.0', '1.0.0', 0],
    ]
    pairs.each do |a, b, expected|
      assert_equal expected, Semver.compare(a, b), "#{a} vs #{b}"
    end
  end
end