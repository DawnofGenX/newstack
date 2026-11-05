NAME := {{ npm_name }}
BUILD := build
LDC ?= ldc2
DFLAGS := -O -release -i -w -de -Isource

SOURCES := source/textstat/counts.d source/textstat/json.d source/textstat/contract.d source/textstat/server.d

.PHONY: all test clean

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): $(SOURCES) source/app.d
	@mkdir -p $(BUILD)
	$(LDC) $(DFLAGS) -of=$(BUILD)/$(NAME) source/app.d

test:
	@mkdir -p $(BUILD)
	$(LDC) -unittest -main -i -w -Isource -of=$(BUILD)/tests test/runtests.d
	@./$(BUILD)/tests
	@echo "all checks passed"

clean:
	rm -rf $(BUILD)
