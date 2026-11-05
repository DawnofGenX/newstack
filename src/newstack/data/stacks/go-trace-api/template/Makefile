NAME := {{ npm_name }}

.PHONY: build test selftest serve clean

build:
	go build -o build/$(NAME) .

test:
	go vet ./...
	go test ./...

selftest: build
	./build/$(NAME) --selftest

serve: build
	./build/$(NAME)

clean:
	rm -rf build
