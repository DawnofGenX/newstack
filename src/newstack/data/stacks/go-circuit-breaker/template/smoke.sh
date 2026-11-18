#!/bin/sh
set -eu
go build -o bin/cb .
./bin/cb --demo | grep -q closed
./bin/cb --demo | grep -q open
echo ok
