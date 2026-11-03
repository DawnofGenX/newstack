# frozen_string_literal: true

require 'json'
require 'sinatra/base'

# A JSON-only HTTP API: a health probe, a greeting, and an echo endpoint.
#
# Modular style: the app is a Sinatra::Base subclass, so `config.ru` boots it and
# `rack-test` drives it in-process without opening a socket.
class App < Sinatra::Base
  configure do
    set :show_exceptions, false
    set :raise_errors, false
  end

  before do
    content_type :json
  end

  get '/health' do
    json(status: 'ok')
  end

  get '/greet/:name' do
    json(message: "Hello, #{params['name']}!")
  end

  post '/echo' do
    json(received: parse_json_body)
  end

  not_found do
    json(error: 'not found')
  end

  helpers do
    def json(payload)
      JSON.generate(payload)
    end

    def parse_json_body
      JSON.parse(request.body.read)
    rescue JSON::ParserError
      halt 400, json(error: 'invalid JSON')
    end
  end
end
