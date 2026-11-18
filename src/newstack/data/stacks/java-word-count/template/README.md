# {{ title }}

{{ description }}

## Usage

```sh
mvn -B package
printf 'the cat sat on the mat' | java -jar target/{{ npm_name }}.jar --top 3
printf 'the cat sat on the mat' | java -jar target/{{ npm_name }}.jar --word The
printf 'one two two' | java -jar target/{{ npm_name }}.jar --all
java -jar target/{{ npm_name }}.jar --help < /dev/null
```

Words are lowercased and stripped of punctuation, so `The`, `the!` and
`THE,` all count as `the`. The ranking sorts by count and breaks ties
alphabetically, `--top N` limits the output, `--all` prints every distinct
word and `--word W` prints a single count. Unknown options exit 2 and an
unreadable stdin exits 1.
