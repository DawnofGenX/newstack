JSONNET ?= jsonnet

build: build/manifest.json

build/manifest.json: config/*.jsonnet lib/*.libsonnet
	@mkdir -p build
	$(JSONNET) -J lib -o build/manifest.json config/render.jsonnet

check:
	./bin/{{ npm_name }} check

test:
	./bin/{{ npm_name }} test

clean:
	rm -rf build

.PHONY: build check test clean
