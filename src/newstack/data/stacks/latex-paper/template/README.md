# {{ title }}

A two-page LaTeX article with a real bibliography and a build that proves the PDF is
the one you meant to write.

```
make build     # latexmk -pdf, two passes plus bibtex
make check     # rebuild, extract the text, assert what a reader sees
make clean     # drop build/
```

The sources are `paper.tex` (preamble, title, `\input`s), `macros.tex` (project
shorthands), `sections/*.tex`, `tables/counts.tex` and `references.bib`.
`check.sh` is the gate: it builds, runs `pdftotext`, and fails on a missing section, a
citation that did not resolve, a `??` placeholder, an overfull line or the wrong page
count.

## Traps this starter already paid for

1. **The double brace is newstack's, not LaTeX's.** The template is rendered before TeX
   ever sees it, and the renderer only substitutes a known placeholder name — so `\title{{{ title }}}`
   becomes `\title{Blog Count}`: the brace that belongs to `\title` survives, the two
   that wrapped the placeholder do not. A placeholder with a single brace
   (`{title}`) is left alone and ends up in the PDF as literal text.
2. **`\n` inside `\texttt{}` is not a newline.** It is an undefined control sequence,
   and with `-halt-on-error` that is a fatal `Undefined control sequence` from inside
   the table cell. Describe the input in words, or write `\textbackslash n`.
3. **`_` and `^` are math-mode only.** A project name containing an underscore breaks
   the nominal `\newcommand{\projectname}{…}` too, which is why the macros use the
   hyphenated `npm_name` rather than the underscored `package_name`.
4. **`latexmk -v` is not "print the version"** in latexmk 4.x — it launches the
   previewer and the step hangs until the job timeout. Use `latexmk --version`, and
   never put `-v` in a Makefile.
5. **One pass is not enough for a citation.** `pdflatex` once gives `[?]`; latexmk
   reruns until the `.aux` and `.bbl` settle. Assert `[1]` only after `make build`
   (which is exactly what `check.sh` does).
6. **`pdftotext -layout` keeps the column layout.** Section numbers sit in their own
   column, so `grep '1 Introduction'` never matches, while plain `pdftotext` drops the
   numbers altogether. Assert heading text, not numbers.
7. **Assert on the extracted text and the log, not on the sources.** A missing
   reference shows up as `??` in the text and as `LaTeX Warning: Reference` in
   `build/paper.log`; a line that is too long shows up as `Overfull \hbox`. Those three
   greps catch most document regressions without a real diff.
8. **`-outdir build` keeps the tree clean** but also means every artefact (`paper.aux`,
   `paper.bbl`, `paper.log`) lives under `build/`, which is what `.gitignore` covers.
   `make clean` removes the directory the same way.
9. **`-silent` does not silence everything.** A clean build still prints
   `Missing bbl file 'build/paper.bbl'` on stderr from the first pass; grep `paper.log`
   for warnings instead of grepping the terminal output.

## Layout

```
paper.tex            preamble, title, abstract, \inputs, bibliography
macros.tex           \projectname, \bytes, \wcnote
sections/            introduction, method, results
tables/counts.tex    the fixture table
references.bib       Knuth (1984/1992) and POSIX wc
check.sh             the gate (build + extract + assert)
Makefile             build / check / clean
```
