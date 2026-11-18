# {{ title }}

{{ description }}

## Usage

```sh
gradle run --args='--a MARTHA --b MARHTA'
gradle run --args='--a recieve --list receive,relieve,believe'
gradle run --args='--a hello --b hallo --threshold 0.9'
gradle test
```

`JaroWinkler.jaro` counts matches inside a `max(len) / 2 - 1` window and halves the transposition
count; `winkler` adds the standard `prefix * 0.1 * (1 - jaro)` boost, capped at four characters.
The CLI prints `jaro=… jaro-winkler=… match=…` for a pair, or a ranked list for `--list`.

## Layout

`src/main/kotlin/{{ package_name }}/JaroWinkler.kt` holds the algorithm, `Main.kt` the CLI, and
`src/test/kotlin/{{ package_name }}/JaroWinklerTest.kt` pins the published example values
(`MARTHA`/`MARHTA` 0.9444 and 0.9611, `DIXON`/`DICKSONX` 0.7667 and 0.8133, `CRATE`/`TRACE` 0.7333
with no prefix boost).
