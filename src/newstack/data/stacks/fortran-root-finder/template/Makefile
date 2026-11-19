FC ?= gfortran
FFLAGS ?= -std=f2018 -fall-intrinsics -Wall -Wextra -O2
APP ?= {{ npm_name }}
SOURCES = src/root_find.f90 src/root_options.f90 src/root_runner.f90
MAIN = src/main.f90
TEST = tests/run_tests.f90

all: build/$(APP)

build/$(APP): $(SOURCES) $(MAIN)
	@mkdir -p build
	$(FC) $(FFLAGS) -J build -o $@ $(SOURCES) $(MAIN)

build/run_tests: $(SOURCES) $(TEST)
	@mkdir -p build
	$(FC) $(FFLAGS) -J build -o $@ $(SOURCES) $(TEST)

test: build/run_tests
	./build/run_tests

clean:
	rm -rf build

.PHONY: all test clean
