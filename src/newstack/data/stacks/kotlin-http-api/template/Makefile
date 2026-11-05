PORT ?= 8080
NAME := {{ npm_name }}
JAR := target/$(NAME).jar

.PHONY: build test serve clean

build:
	mvn -q -B -DskipTests package

test: build
	java -jar $(JAR) --selftest

serve: build
	PORT=$(PORT) java -jar $(JAR)

clean:
	mvn -q clean
