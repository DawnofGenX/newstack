# {{ title }}

{{ description }}

## Usage

```sh
mvn -B package
printf 'PUT a 1\nPUT b 2\nGET a\nKEYS\nSTATS\n' | java -jar target/{{ npm_name }}.jar -c 2
```

Commands: `PUT key value`, `GET key`, `PEEK key`, `DEL key`, `KEYS`, `STATS`,
`CLEAR`, `QUIT`. `-c/--capacity` sets the capacity (default 3).
