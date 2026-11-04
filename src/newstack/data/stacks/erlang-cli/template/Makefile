ERLC ?= erlc
ERL ?= erl
EBIN := ebin
LIB_SOURCES := $(wildcard lib/*.erl)
TEST_SOURCES := $(wildcard test/*.erl)
LIB_BEAMS := $(patsubst lib/%.erl,$(EBIN)/%.beam,$(LIB_SOURCES))
TEST_BEAMS := $(patsubst test/%.erl,$(EBIN)/%.beam,$(TEST_SOURCES))
MODULES := textstat_counts_tests textstat_options_tests textstat_runner_tests

.PHONY: all test clean

all: $(LIB_BEAMS)

$(EBIN)/%.beam: lib/%.erl | $(EBIN)
	$(ERLC) -Werror +debug_info -o $(EBIN) $<

$(EBIN)/%.beam: test/%.erl | $(EBIN)
	$(ERLC) -Werror +debug_info -o $(EBIN) $<

$(EBIN):
	mkdir -p $(EBIN)

test: all $(TEST_BEAMS)
	$(ERL) -noshell -pa $(EBIN) -eval 'case eunit:test([$(shell echo $(MODULES) | sed "s/ /,/g")], []) of ok -> halt(0); _ -> halt(1) end.'

clean:
	rm -rf $(EBIN)
