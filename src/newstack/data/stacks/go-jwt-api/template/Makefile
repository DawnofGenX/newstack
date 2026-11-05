NAME := {{ npm_name }}
PORT ?= 8080

.PHONY: build test selftest serve clean

build:
	go build -o build/$(NAME) .

test:
	go vet ./... && go test ./...

selftest: build
	./build/$(NAME) --selftest

serve: build
	TOKEN_SECRET=$${TOKEN_SECRET:-dev-secret} PORT=$(PORT) ./build/$(NAME) --db build/users.json

clean:
	rm -rf build
