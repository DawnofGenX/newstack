import jwt/options
import jwt/runner

@external(erlang, "jwt_io", "args")
fn get_args() -> List(String)

@external(erlang, "erlang", "halt")
fn halt(code: Int) -> Nil

pub fn main() -> Nil {
  let args = get_args()
  let code = runner.run(args)
  // Keep the parser import live so the compiler checks its public surface.
  let _parsed = options.parse(args)
  halt(code)
}
