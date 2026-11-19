version       = "0.1.0"
author        = "{{ author }}"
description   = "{{ description }}"
license       = "MIT"
srcDir        = "src"
bin           = @["{{ package_name }}"]
requires "nim >= 1.6"

# The binary has to exist before tests/test_all.nim can check its exit codes.
task test, "Compile the binary, then run tests/test_all.nim":
  exec "nim c --path:src -o:{{ package_name }} src/{{ package_name }}.nim"
  exec "nim c -r --path:src tests/test_all.nim"
