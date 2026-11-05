# frozen_string_literal: true

require_relative "lib/textstat"

Gem::Specification.new do |spec|
  spec.name = "{{ npm_name }}"
  spec.version = Textstat::VERSION
  spec.summary = "{{ description }}"
  spec.description = "Counts lines, words and bytes, wc-style, with a testable core."
  spec.authors = ["{{ author }}"]
  spec.email = ["{{ email }}"]
  spec.license = "MIT"
  spec.required_ruby_version = ">= 3.2"
  spec.files = Dir["lib/**/*.rb", "bin/*", "README.md", "LICENSE"]
  spec.bindir = "bin"
  spec.executables = ["{{ npm_name }}"]
  spec.require_paths = ["lib"]
  spec.add_development_dependency "minitest", "~> 5.20"
  spec.add_development_dependency "rake", "~> 13.2"
end
