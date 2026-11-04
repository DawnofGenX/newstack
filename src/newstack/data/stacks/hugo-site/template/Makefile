HUGO ?= hugo
DEST ?= public
PORT ?= 1313

.PHONY: all build test serve clean

all: build

build:
	$(HUGO) --gc --cleanDestinationDir --destination $(DEST)

test:
	./tests/run_tests.sh

serve:
	$(HUGO) server --bind 127.0.0.1 --port $(PORT)

clean:
	rm -rf $(DEST) resources/_gen .hugo_build.lock
