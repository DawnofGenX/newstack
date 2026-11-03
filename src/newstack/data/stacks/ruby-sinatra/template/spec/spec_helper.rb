# frozen_string_literal: true

ENV['APP_ENV'] = 'test'

require 'rack/test'
require 'rspec'
require_relative '../app'

RSpec.configure do |config|
  config.include Rack::Test::Methods
  config.disable_monkey_patching!
  config.order = :random
  config.expect_with(:rspec) { |c| c.syntax = :expect }
end

# rack-test drives the app in-process: no socket, no port, no server to boot.
def app
  App
end
