NAME := {{ npm_name }}
BUILD := build

CXX ?= c++
CPPFLAGS := -Iinclude -D_POSIX_C_SOURCE=200809L
CXXFLAGS := -std=c++17 -O2 -g -Wall -Wextra -Wpedantic -Werror

LIB_SRCS := src/counts.cpp src/json.cpp src/contract.cpp src/http.cpp
LIB_OBJS := $(patsubst src/%.cpp,$(BUILD)/%.o,$(LIB_SRCS))
TEST_SRCS := tests/main.cpp tests/test_counts.cpp tests/test_json.cpp tests/test_contract.cpp
TEST_OBJS := $(patsubst tests/%.cpp,$(BUILD)/tests/%.o,$(TEST_SRCS))

.PHONY: all test clean

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): $(LIB_OBJS) $(BUILD)/main.o
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/main.o: src/main.cpp | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

$(BUILD)/%.o: src/%.cpp | $(BUILD)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

$(BUILD)/tests/%.o: tests/%.cpp | $(BUILD)/tests
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

$(BUILD)/tests/run: $(TEST_OBJS) $(LIB_OBJS) | $(BUILD)/tests
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD) $(BUILD)/tests:
	mkdir -p $@

test: $(BUILD)/tests/run
	./$(BUILD)/tests/run

clean:
	rm -rf $(BUILD)
