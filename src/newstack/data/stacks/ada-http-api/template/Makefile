NAME := {{ npm_name }}
BUILD := build
GNATMAKE ?= gnatmake
FLAGS := -O2 -gnatwa -gnatwe -gnata -Isrc

SOURCES := $(wildcard src/*.adb src/textstat-*.adb src/textstat-*.ads)

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): $(SOURCES)
	mkdir -p $(BUILD)/obj
	$(GNATMAKE) $(FLAGS) -D $(BUILD)/obj -o $(BUILD)/$(NAME) src/app.adb

test: $(SOURCES) tests/run_tests.adb
	mkdir -p $(BUILD)/obj
	$(GNATMAKE) $(FLAGS) -D $(BUILD)/obj -o $(BUILD)/run-tests tests/run_tests.adb
	./$(BUILD)/run-tests

clean:
	rm -rf $(BUILD)
