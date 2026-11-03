# frozen_string_literal: true

RSpec.describe App do
  it 'reports healthy' do
    get '/health'

    expect(last_response.status).to eq(200)
    expect(last_response.content_type).to include('application/json')
    expect(JSON.parse(last_response.body)).to eq('status' => 'ok')
  end

  it 'greets a name from the path' do
    get '/greet/ada'

    expect(last_response.status).to eq(200)
    expect(JSON.parse(last_response.body)).to eq('message' => 'Hello, ada!')
  end

  it 'echoes a posted JSON body' do
    post '/echo', JSON.generate('hello' => 'world'), 'CONTENT_TYPE' => 'application/json'

    expect(last_response.status).to eq(200)
    expect(JSON.parse(last_response.body)).to eq('received' => { 'hello' => 'world' })
  end

  it 'rejects a body that is not JSON' do
    post '/echo', 'not json', 'CONTENT_TYPE' => 'application/json'

    expect(last_response.status).to eq(400)
    expect(JSON.parse(last_response.body)).to eq('error' => 'invalid JSON')
  end

  it 'answers unknown routes with JSON 404' do
    get '/nope'

    expect(last_response.status).to eq(404)
    expect(last_response.content_type).to include('application/json')
    expect(JSON.parse(last_response.body)).to eq('error' => 'not found')
  end
end
