LDC ?= ldc2

SOURCES := $(wildcard source/*.d)
TESTS := $(wildcard tests/*.d)

build: build/app

build/app: $(SOURCES)
	@mkdir -p build
	$(LDC) -O -Isource -of=build/app $(SOURCES)

build/tests: $(SOURCES) $(TESTS)
	@mkdir -p build
	$(LDC) -unittest -Isource -Itests -of=build/tests source/floatbits.d tests/harness.d tests/floatbits_test.d tests/test_main.d

test: build build/tests
	./build/tests

clean:
	rm -rf build

.PHONY: build test clean