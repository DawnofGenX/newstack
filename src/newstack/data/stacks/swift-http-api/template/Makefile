NAME := {{ npm_name }}
BUILD := build
SWIFTC ?= swiftc
SWIFTFLAGS := -O -warnings-as-errors

SOURCES := $(shell find src -name '*.swift')
TESTS := $(shell find tests -name '*.swift')

.PHONY: all test clean

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): $(SOURCES) $(TESTS)
	@mkdir -p $(BUILD)
	$(SWIFTC) $(SWIFTFLAGS) $(SOURCES) $(TESTS) -o $@

test: all
	$(BUILD)/$(NAME) --selftest

clean:
	rm -rf $(BUILD)
