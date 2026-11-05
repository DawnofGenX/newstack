NAME := {{ npm_name }}
PORT ?= 5470

.PHONY: build release test selftest serve smoke clean

build:
	cargo build

release:
	cargo build --release

test:
	cargo test

selftest: build
	./target/debug/$(NAME) --selftest

serve: release
	PORT=$(PORT) ./target/release/$(NAME)

smoke: release
	PORT=$(PORT) bash smoke.sh

clean:
	cargo clean
