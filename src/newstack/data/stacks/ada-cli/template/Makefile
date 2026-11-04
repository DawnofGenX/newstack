#  Two phases: gnatmake compiles and binds, the wrapper just runs the binary.
#  APP is overridable so a copy of this project can be built under any name.
APP ?= {{ npm_name }}
GNATMAKE ?= gnatmake
OBJ := obj
SOURCES := $(wildcard src/*.ads src/*.adb)
TEST_SOURCES := $(wildcard tests/*.ads tests/*.adb)

all: build/$(APP)

build/$(APP): $(SOURCES)
	@mkdir -p build $(OBJ)
	$(GNATMAKE) -gnatwa -I./src -D $(OBJ) -o build/$(APP) src/main.adb

test: build/tests
	./build/tests

build/tests: $(TEST_SOURCES) $(SOURCES)
	@mkdir -p build $(OBJ)
	$(GNATMAKE) -gnatwa -I./src -I./tests -D $(OBJ) -o build/tests tests/run_tests.adb

clean:
	rm -rf build $(OBJ)

.PHONY: all test clean
