# {{ title }}

NAME := {{ npm_name }}
CXX ?= g++
CXXFLAGS := -std=c++17 -O2 -g -Wall -Wextra -Wpedantic -Werror
CPPFLAGS := -Iinclude

SRCS := src/flatten.cpp src/main.cpp
OBJS := $(SRCS:.cpp=.o)

.PHONY: all test clean

all: $(NAME)

$(NAME): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^

%.o: %.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

test: tests/test_flatten
	./tests/test_flatten

tests/test_flatten: tests/test_flatten.cpp src/flatten.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -o $@ tests/test_flatten.cpp src/flatten.cpp

clean:
	rm -f $(NAME) $(OBJS) tests/test_flatten