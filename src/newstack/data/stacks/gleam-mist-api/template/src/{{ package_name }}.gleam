import gleam/bit_array
import gleam/bytes_tree
import gleam/erlang/process
import gleam/http/request
import gleam/http/response
import gleam/int
import gleam/option
import gleam/result

import {{ package_name }}/contract
import mist

const default_port = 8080

const max_body_bytes = 65_536

@external(erlang, "{{ package_name }}_env_ffi", "get_env")
fn get_env(name: String) -> Result(String, Nil)

fn read_port() -> Int {
  case get_env("PORT") {
    Ok(value) ->
      case int.parse(value) {
        Ok(port) -> port
        Error(_) -> default_port
      }
    Error(_) -> default_port
  }
}

fn json_body(body: String) -> mist.ResponseData {
  mist.Bytes(bytes_tree.from_string(body))
}

fn handler(
  req: request.Request(BitArray),
) -> response.Response(mist.ResponseData) {
  let reply =
    contract.route(
      req.method,
      req.path,
      option.unwrap(req.query, ""),
      bit_array.to_string(req.body) |> result.unwrap(""),
    )
  response.new(reply.status)
  |> response.set_header("content-type", "application/json")
  |> response.set_body(json_body(reply.body))
}

pub fn main() -> Nil {
  let too_large =
    response.new(413)
    |> response.set_header("content-type", "application/json")
    |> response.set_body(json_body("{\"error\":\"body_too_large\"}"))

  let assert Ok(_) =
    mist.new(handler)
    |> mist.read_request_body(
      bytes_limit: max_body_bytes,
      failure_response: too_large,
    )
    |> mist.bind("127.0.0.1")
    |> mist.port(read_port())
    |> mist.start()

  process.sleep_forever()
}
