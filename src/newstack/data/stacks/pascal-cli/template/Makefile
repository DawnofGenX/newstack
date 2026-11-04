FPC ?= fpc
APP ?= {{ npm_name }}
OBJ = obj
BUILD = build
UNITS = src/textstat_counts.pas src/textstat_options.pas src/textstat_runner.pas
# -B keeps a stale .ppu from masking an edit: fpc compares timestamps with
# one-second resolution, so two builds inside the same second can otherwise reuse
# a unit that just changed.
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
