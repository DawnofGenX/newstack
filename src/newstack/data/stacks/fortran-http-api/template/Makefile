NAME := {{ npm_name }}
FC ?= gfortran
FFLAGS ?= -std=gnu -Wall -Wextra -Werror -O2
SOURCES := src/bytes_m.f90 src/counts_m.f90 src/json_m.f90 src/contract_m.f90 src/server_m.f90
TESTS := tests/selftest_m.f90
BUILD := build

.PHONY: build test serve clean

build:
	@mkdir -p $(BUILD)
	$(FC) $(FFLAGS) -J$(BUILD) -o $(BUILD)/$(NAME) $(SOURCES) $(TESTS) src/main.f90

test: build
	./$(BUILD)/$(NAME) --selftest

serve: build
	PORT=$${PORT:-8080} ./$(BUILD)/$(NAME)

clean:
	rm -rf $(BUILD)
