#!/bin/sh
set -eu
go build -o bin/bloom .
./bin/bloom create /tmp/bf.json --bits 1024 --hashes 4
./bin/bloom add /tmp/bf.json hello
./bin/bloom check /tmp/bf.json hello | grep -q true
./bin/bloom stats /tmp/bf.json | grep -q bits
echo ok
