# Ada duration CLI: parse and format ISO-8601 / human durations.
APP ?= {{ npm_name }}
GNATMAKE ?= gnatmake
OBJ := obj

all: build/$(APP)

build/$(APP): src/*.ads src/*.adb
	@mkdir -p build $(OBJ)
	$(GNATMAKE) -gnatwa -I./src -D $(OBJ) -o build/$(APP) src/main.adb

test: build/tests
	./build/tests

build/tests: tests/*.adb src/*.ads src/*.adb
	@mkdir -p build $(OBJ)
	$(GNATMAKE) -gnatwa -I./src -I./tests -D $(OBJ) -o build/tests tests/run_tests.adb

clean:
	rm -rf build $(OBJ)

.PHONY: all test clean