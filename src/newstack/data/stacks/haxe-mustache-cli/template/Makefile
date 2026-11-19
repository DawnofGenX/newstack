HAXE ?= haxe
NEKO ?= neko

SOURCES := $(wildcard src/*.hx)
TESTS := $(wildcard tests/*.hx)

build: build/app.n

build/app.n: build.hxml $(SOURCES)
	@mkdir -p build
	$(HAXE) build.hxml

build/tests.n: test.hxml $(SOURCES) $(TESTS)
	@mkdir -p build
	$(HAXE) test.hxml

test: build build/tests.n
	$(NEKO) build/tests.n

clean:
	rm -rf build

.PHONY: build test clean
