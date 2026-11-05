LDC ?= ldc2

SOURCES := $(wildcard source/*.d)
TESTS := $(wildcard tests/*.d)

build: build/app

build/app: $(SOURCES)
	@mkdir -p build
	$(LDC) -i -O -Isource -of=build/app source/app.d

build/tests: $(SOURCES) $(TESTS)
	@mkdir -p build
	$(LDC) -i -Isource -Itests -of=build/tests tests/test_main.d

test: build build/tests
	./build/tests

parity: build
	bash tests/parity.sh

clean:
	rm -rf build .parity

.PHONY: build test parity clean
