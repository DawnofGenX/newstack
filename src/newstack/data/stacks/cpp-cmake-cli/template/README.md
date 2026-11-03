# {{ title }}

{{ description }}

A dependency-free C++20 command line tool: counting lives in a `textstat`
library (`include/textstat/`, `src/textstat/`) so it can be tested directly,
and `src/main.cpp` is a thin binary that turns argv into output and an exit
code. CMake builds both targets; CTest runs the tests.

## Layout

```
CMakeLists.txt              textstat library + {{ npm_name }} executable, C++20, warnings on
include/textstat/counters.hpp   Counts struct and count_text()
include/textstat/options.hpp    option parsing and help text
src/textstat/counters.cpp       line / word / byte counting
src/textstat/options.cpp        hand-rolled argv parsing, no getopt
src/main.cpp                    reads files or stdin, prints counts, sets the exit code
tests/                          tiny assert header, unit tests, and a CLI test driven by ctest
```

No third-party dependencies: no GoogleTest, no package fetches. The template
configures, builds and tests offline.

## Build

```console
$ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
$ cmake --build build --parallel
```

## Run

```console
$ ./build/{{ npm_name }} --help
$ ./build/{{ npm_name }} README.md
$ printf 'one two\nthree\n' | ./build/{{ npm_name }} -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ ctest --test-dir build --output-on-failure
```

## Formatting

`.clang-format` is LLVM-based at 100 columns:

```console
$ clang-format -i src/*.cpp src/textstat/*.cpp include/textstat/*.hpp
```

## License

MIT — see [LICENSE](LICENSE).
