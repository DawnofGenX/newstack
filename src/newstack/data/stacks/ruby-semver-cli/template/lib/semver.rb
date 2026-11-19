# frozen_string_literal: true

# Semantic versioning 2.0.0: parse, compare and validate version strings.
#
# A version is MAJOR.MINOR.PATCH with optional pre-release and build metadata:
#   1.2.3
#   1.2.3-rc.1
#   1.2.3+build.42
module Semver
  VERSION_RE = /\A(?<major>0|[1-9]\d*)\.(?<minor>0|[1-9]\d*)\.(?<patch>0|[1-9]\d*)(?:-(?<pre>[0-9A-Za-z\-\.]+))?(?:\+(?<build>[0-9A-Za-z\-\.]+))?\z/

  class Error < StandardError; end

  Version = Struct.new(:major, :minor, :patch, :pre, :build, keyword_init: true) do
    def to_s
      base = "#{major}.#{minor}.#{patch}"
      base += "-#{pre}" unless pre.nil? || pre.empty?
      base += "+#{build}" unless build.nil? || build.empty?
      base
    end

    def <=>(other)
      Semver.compare(self, other)
    end
  end

  module_function

  def parse(text)
    m = VERSION_RE.match(text.to_s.strip)
    raise Error, "invalid semantic version: #{text.inspect}" if m.nil?

    Version.new(
      major: m[:major].to_i,
      minor: m[:minor].to_i,
      patch: m[:patch].to_i,
      pre: m[:pre],
      build: m[:build]
    )
  end

  def valid?(text)
    VERSION_RE.match?(text.to_s.strip)
  end

  # Returns -1, 0 or 1.
  def compare(a, b)
    va = a.is_a?(Version) ? a : parse(a)
    vb = b.is_a?(Version) ? b : parse(b)

    [va.major, va.minor, va.patch].each_with_index do |_, i|
      x = [va.major, va.minor, va.patch][i]
      y = [vb.major, vb.minor, vb.patch][i]
      return -1 if x < y
      return 1 if x > y
    end

    # Pre-release: a version without pre-release is greater.
    a_pre = va.pre
    b_pre = vb.pre
    a_has = !(a_pre.nil? || a_pre.empty?)
    b_has = !(b_pre.nil? || b_pre.empty?)

    return 0 unless a_has || b_has
    return 1 unless a_has # a release > a pre-release
    return -1 unless b_has

    # Compare pre-release identifiers.
    a_ids = a_pre.split('.')
    b_ids = b_pre.split('.')
    len = [a_ids.length, b_ids.length].max
    len.times do |i|
      ai = a_ids[i]
      bi = b_ids[i]
      return -1 if ai.nil?
      return 1 if bi.nil?
      # numeric vs alphanumeric
      a_num = ai.match?(/\A\d+\z/)
      b_num = bi.match?(/\A\d+\z/)
      if a_num && b_num
        x = ai.to_i
        y = bi.to_i
        return -1 if x < y
        return 1 if x > y
      elsif a_num != b_num
        # numeric identifiers have lower precedence than alphanumeric
        return -1 if a_num
        return 1
      else
        cmp = ai <=> bi
        return cmp unless cmp.zero?
      end
    end
    0
  end
end