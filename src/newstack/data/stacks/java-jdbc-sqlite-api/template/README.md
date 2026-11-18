# {{ title }}

{{ description }}

## Run

```sh
mvn -B package
java -jar target/{{ npm_name }}.jar
```

In another terminal:

```sh
curl http://127.0.0.1:5553/health
```

Requires Java 21 and Maven.

## Test

```sh
mvn -B test
```