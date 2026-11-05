NAME := {{ npm_name }}
BUILD := build
FPC ?= fpc
FPCFLAGS := -O2 -Mobjfpc -Sh -vw -Fusrc -FU$(BUILD)/units -FE$(BUILD)

.PHONY: all test clean

all: $(BUILD)/$(NAME)

$(BUILD)/$(NAME): src/app.pas $(wildcard src/counts.pas src/jsonbody.pas src/contract.pas src/server.pas)
	@mkdir -p $(BUILD)/units
	$(FPC) $(FPCFLAGS) -o$(BUILD)/$(NAME) src/app.pas

test:
	@mkdir -p $(BUILD)/units
	$(FPC) $(FPCFLAGS) -o$(BUILD)/run-tests tests/run_tests.pas
	./$(BUILD)/run-tests

clean:
	rm -rf $(BUILD)
