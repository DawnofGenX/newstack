require "kemal"

require "./contract"

module {{ class_name }}
  # The socket layer: every route funnels into `Contract.route`, so the wire
  # behaviour is exactly what the specs describe.
  def self.respond(env : HTTP::Server::Context, method : String) : String
    body = env.request.body.try(&.gets_to_end)
    reply = Contract.route(method, env.request.path, env.request.query, body)
    env.response.status_code = reply.status
    env.response.content_type = "application/json"
    reply.body.to_json
  end

  def self.start(port : Int32) : Nil
    Kemal.config.port = port
    Kemal.config.env = "production"
    get "/health" { |env| respond(env, "GET") }
    get "/stats" { |env| respond(env, "GET") }
    post "/stats" { |env| respond(env, "POST") }
    error 404 { |env| respond(env, env.request.method) }
    error 405 { |env| respond(env, env.request.method) }
    Kemal.run
  end
end
