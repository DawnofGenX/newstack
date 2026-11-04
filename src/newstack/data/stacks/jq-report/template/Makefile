SHELL := /bin/sh

.PHONY: all lint test report clean

all: lint test

lint:            # every filter must compile
	./bin/{{ npm_name }} lint

test:            # unit and command-line suites
	./tests/run_tests.sh

report:          # every report over the sample log
	@for name in $$(./bin/{{ npm_name }} filters); do \
		printf '== %s\n' "$$name"; \
		./bin/{{ npm_name }} run "$$name" data/sample.json; \
	done

clean:
	rm -rf .parity
