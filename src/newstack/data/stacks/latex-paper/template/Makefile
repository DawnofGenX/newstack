NAME := {{ npm_name }}
LATEXMK ?= latexmk
BUILD := build
TEXFLAGS := -silent -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=$(BUILD)

.PHONY: build check clean

build:
	mkdir -p $(BUILD)
	$(LATEXMK) $(TEXFLAGS) paper.tex

check: build
	bash check.sh

clean:
	$(LATEXMK) -C -outdir=$(BUILD) paper.tex
	rm -rf $(BUILD)
