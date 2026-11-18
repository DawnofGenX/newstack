# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/{{ npm_name }} .
./bin/{{ npm_name }} -template conf.tmpl -data data.json
./bin/{{ npm_name }} -template conf.tmpl -data data.json -out rendered.conf
```
