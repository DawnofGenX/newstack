# {{ title }}

{{ description }}

A small Java 21 Spring Boot 3 web service: counting lives in a pure service
(`StatsService`) so tests drive it directly, and `StatsController` exposes the
counts over HTTP. Maven builds the jar and runs the JUnit 5 + MockMvc suite.

## Layout

```
pom.xml                            Spring Boot 3 parent, Java 21, web + test starters
src/main/java/com/example/textstat/Application.java      Spring Boot entry point
src/main/java/com/example/textstat/Stats.java           line / word / byte record
src/main/java/com/example/textstat/StatsService.java    pure counting, no I/O
src/main/java/com/example/textstat/StatsController.java GET /stats and GET /
src/main/resources/application.properties               app name and port
src/test/java/com/example/textstat/                      JUnit 5 + MockMvc tests
```

## Build

```console
$ mvn -B -ntp package
```

A Maven wrapper is included, so `./mvnw -B -ntp package` works on machines
without a system Maven.

The jar is `target/{{ npm_name }}.jar`.

## Run

```console
$ java -jar target/{{ npm_name }}.jar
```

The app listens on port 8080 (`server.port` in
`src/main/resources/application.properties`). Run it on another port without editing the
file:

```console
$ java -jar target/{{ npm_name }}.jar --server.port=18080
```

Then:

```console
$ curl "http://localhost:8080/stats?text=hello%20world"
{"lines":0,"words":2,"bytes":11}
$ curl http://localhost:8080/
{"message":"hello"}
```

## Test

```console
$ mvn -B -ntp test
```

## License

MIT — see [LICENSE](LICENSE).
