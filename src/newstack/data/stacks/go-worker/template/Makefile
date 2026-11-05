NAME := {{ npm_name }}

.PHONY: build test selftest demo clean

build:
	go build -o bin/$(NAME) .

test:
	go test ./...

selftest: build
	./bin/$(NAME) --selftest

demo: build
	./run.sh

clean:
	rm -rf bin
