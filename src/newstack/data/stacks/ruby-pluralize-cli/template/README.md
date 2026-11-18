# {{ title }}

{{ description }}

## Usage

```sh
rake test

bin/{{ npm_name }} plural cat person sheep      # cats, people, sheep
bin/{{ npm_name }} singular cats people boxes   # cat, person, box
bin/{{ npm_name }} count --count 3 person       # 3 people
printf 'baby\nknife\n' | bin/{{ npm_name }} plural
bin/{{ npm_name }} plural --file words.txt
```

Rules are ordered and the first match wins, so `city` becomes `cities` before
the generic `s` rule while `day` stays `days`. Irregulars cover the common
Germanic and Latin forms, and uncountables (`sheep`, `series`, `information`)
pass through untouched. Unknown commands and options exit 2, unreadable files
exit 1.
