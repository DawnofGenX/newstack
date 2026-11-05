# {{ title }} — plain make, no dependencies.
#
# `make`       builds the binary into build/
# `make test`  builds and runs the assert-based test suite
# `make clean` removes build/
#
# Everything is C11 with warnings promoted to errors, so a warning in the
# generated project is a build failure from the first commit.

NAME := {{ npm_name }}
BUILD := build

CC ?= cc
CPPFLAGS := -Iinclude -D_POSIX_C_SOURCE=200809L
CFLAGS := -std=c11 -O2 -g -Wall -Wextra -Wpedantic -Werror
LDLIBS :=

LIB_SRCS := src/counters.c src/options.c
LIB_OBJS := $(LIB_SRCS:src/%.c=$(BUILD)/%.o)
LIB_HDRS := include/textstat/counters.h include/textstat/options.h

TEST_SRCS := $(wildcard tests/*.c)
TEST_OBJS := $(TEST_SRCS:tests/%.c=$(BUILD)/tests-%.o)

.PHONY: all test clean

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): $(BUILD)/main.o $(LIB_OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

$(BUILD)/%.o: src/%.c $(LIB_HDRS) | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(BUILD)/main.o: src/main.c $(LIB_HDRS) | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(BUILD)/tests-%.o: tests/%.c tests/check.h $(LIB_HDRS) | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -Itests -c -o $@ $<

$(BUILD)/tests: $(TEST_OBJS) $(LIB_OBJS) | $(BUILD)
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

test: $(BUILD)/tests
	./$(BUILD)/tests

$(BUILD):
	mkdir -p $(BUILD)

clean:
	rm -rf $(BUILD)
