# {{ npm_name }} — Ktor 3 text-statistics service
# Targets use the JDK 21 + Maven 3.8.7 already on PATH.

MVN := mvn -q -B
JAR := target/{{ npm_name }}.jar

.PHONY: build test selftest serve clean

build:
	$(MVN) -DskipTests package

test:
	$(MVN) test

selftest: $(JAR)
	java -jar $(JAR) --selftest

serve: $(JAR)
	java -jar $(JAR)

clean:
	$(MVN) clean

$(JAR): src/main/kotlin/textstat/*.kt pom.xml
	$(MVN) -DskipTests package
