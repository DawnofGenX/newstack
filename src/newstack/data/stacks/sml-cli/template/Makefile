MLTON ?= mlton

SOURCES := $(wildcard src/*.sml)
TESTS := $(wildcard tests/*.sml)

build: build/app

build/app: app.mlb $(SOURCES)
	@mkdir -p build
	$(MLTON) -output build/app app.mlb

build/tests: tests.mlb $(SOURCES) $(TESTS)
	@mkdir -p build
	$(MLTON) -output build/tests tests.mlb

test: build build/tests
	./build/tests

parity: build
	bash tests/parity.sh

clean:
	rm -rf build .parity

.PHONY: build test parity clean
