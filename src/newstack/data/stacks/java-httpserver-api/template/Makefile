# {{ title }} — plain make and javac, no build tool, no dependencies.
#
# `make`       compiles the service into build/classes
# `make test`  compiles and runs the dependency-free check suite
# `make clean` removes build/
#
# Every file is compiled with -Xlint:all and warnings promoted to errors, so a
# warning in the generated project is a build failure from the first commit.

NAME := {{ npm_name }}
BUILD := build
JAVAC ?= javac
JAVA ?= java
JAVACFLAGS := -Xlint:all -Werror -d $(BUILD)/classes

SOURCES := $(shell find src/main/java -name '*.java')
TESTS := $(shell find tests -name '*.java')

.PHONY: all test clean

all: $(BUILD)/classes/.built

$(BUILD)/classes/.built: $(SOURCES)
	@mkdir -p $(BUILD)/classes
	$(JAVAC) $(JAVACFLAGS) $(SOURCES)
	@touch $@

test: all
	$(JAVAC) -Xlint:all -Werror -cp $(BUILD)/classes -d $(BUILD)/test-classes $(TESTS)
	$(JAVA) -cp $(BUILD)/classes:$(BUILD)/test-classes RunTests

clean:
	rm -rf $(BUILD)
