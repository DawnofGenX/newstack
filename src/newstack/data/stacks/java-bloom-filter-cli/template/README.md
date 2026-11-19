# {{ title }}

{{ description }}

Bloom filter membership testing from the command line.

## Usage

```console
$ printf 'apple\nbanana\n' | java -jar target/{{ npm_name }}.jar contains apple
probably
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success |
| 1 | bad input |
| 2 | usage error |

## Test

```console
$ mvn -B test
$ bash smoke.sh
```