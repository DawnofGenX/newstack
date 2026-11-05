NAME := {{ npm_name }}
PORT ?= 5490
BIN_DIR := bin
BUILD_DIR := build
PKG := ./...

.PHONY: build test selftest smoke clean fmt vet

build:
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(NAME) .
	@echo "built $(BUILD_DIR)/$(NAME)"

test:
	go vet $(PKG)
	go test $(PKG)

selftest: build
	./$(BUILD_DIR)/$(NAME) --selftest

smoke: build
	@PORT=$(PORT) bash smoke.sh

fmt:
	gofmt -w .

vet:
	go vet $(PKG)

clean:
	rm -rf $(BUILD_DIR)
