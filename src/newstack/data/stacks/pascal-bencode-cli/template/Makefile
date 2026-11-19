FPC ?= fpc
APP ?= {{ npm_name }}
OBJ = obj
BUILD = build
UNITS = src/bencode.pas
FPCFLAGS = -B -O2 -v0 -Fu./src -FU./$(OBJ) -FE./$(BUILD)

all: $(BUILD)/$(APP)

$(BUILD)/$(APP): src/main.pas $(UNITS)
	@mkdir -p $(OBJ) $(BUILD)
	$(FPC) $(FPCFLAGS) -o$(APP) src/main.pas

test: $(BUILD)/run_tests
	./$(BUILD)/run_tests

$(BUILD)/run_tests: tests/run_tests.pas $(UNITS)
	@mkdir -p $(OBJ) $(BUILD)
	$(FPC) $(FPCFLAGS) tests/run_tests.pas

clean:
	rm -rf $(OBJ) $(BUILD)

.PHONY: all test clean
