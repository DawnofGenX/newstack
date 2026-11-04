MD := mdbook

.PHONY: all build check test serve clean

all: check test build

build:            # render the static site into book/
	$(MD) build

check:            # every relative link resolves and every page is in the summary
	./tools/check-links.sh

test:             # the checker's own suite
	./tests/run_tests.sh

serve:            # live preview on http://localhost:3000
	$(MD) serve --open

clean:
	rm -rf book
