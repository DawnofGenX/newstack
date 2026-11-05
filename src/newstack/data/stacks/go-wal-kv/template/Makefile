NAME := {{ npm_name }}
PORT ?= 5491

.PHONY: build test selftest smoke clean

build:
	mkdir -p build
	go build -o build/$(NAME) .

test:
	go test ./...

selftest: build
	./build/$(NAME) --selftest

smoke: build
	PORT=$(PORT) bash smoke.sh

clean:
	rm -rf build
	rm -rf wal
