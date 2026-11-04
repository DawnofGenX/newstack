APP ?= {{ npm_name }}
BUILD = build
COBFLAGS = -free -O2
SRC = src/main.cob src/textstat-options.cob src/textstat-counts.cob src/textstat-runner.cob

all: $(BUILD)/$(APP)

$(BUILD)/$(APP): $(SRC) | $(BUILD)
	cobc -x $(COBFLAGS) -o $@ $(SRC)

$(BUILD)/textstat-tests: tests/textstat-tests.cob src/textstat-counts.cob src/textstat-options.cob | $(BUILD)
	cobc -x $(COBFLAGS) -o $@ tests/textstat-tests.cob src/textstat-counts.cob src/textstat-options.cob

$(BUILD):
	mkdir -p $(BUILD)

test: $(BUILD)/$(APP) $(BUILD)/textstat-tests
	bash tests/run_tests.sh $(BUILD)/$(APP)

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
