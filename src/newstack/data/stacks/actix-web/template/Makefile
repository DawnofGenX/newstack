NAME := {{ npm_name }}

.PHONY: build test selftest serve smoke clean

build:
	cargo build --release

test:
	cargo test

selftest: build
	./target/release/$(NAME) --selftest

serve: build
	./target/release/$(NAME)

smoke: build
	bash smoke.sh

clean:
	cargo clean
