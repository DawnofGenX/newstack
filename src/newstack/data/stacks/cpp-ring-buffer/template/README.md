# {{ project_name }}

Fixed-capacity ring buffer with a trace-driven CLI.

## Usage

```sh
cmake -S . -B build
cmake --build build
printf 'push 1\npush 2\npop\nsize\n' | ./build/{{ npm_name }}
./build/{{ npm_name }} --help
```

Exit codes: 0 success, 2 usage or parse error.