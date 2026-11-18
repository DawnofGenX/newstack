# {{ title }}

{{ description }}

## Usage

```sh
mvn -B package
java -jar target/{{ npm_name }}.jar config.properties db.host localhost
```

## Test

```sh
mvn -B test
```
