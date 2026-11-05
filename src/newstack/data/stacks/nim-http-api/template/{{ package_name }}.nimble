version       = "0.1.0"
author        = "Author"
description   = "A small JSON service that counts lines, words and bytes."
license       = "MIT"
srcDir        = "src"
bin           = @["{{ package_name }}"]
requires "nim >= 1.6.0"

task test, "Run the test suite":
  exec "nim c -r --hints:off tests/test_all.nim"

task check, "Compile every module without running anything":
  exec "nim check --hints:off src/{{ package_name }}.nim"
