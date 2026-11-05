NAME := {{ npm_name }}
PORT ?= 5481

.PHONY: build test selftest smoke clean

build:
	mkdir -p build
	go build -o build/$(NAME) .

test:
	go vet ./...
	go test ./...

selftest: build
	./build/$(NAME) --selftest

smoke:
	PORT=$(PORT) bash smoke.sh

clean:
	rm -rf build
