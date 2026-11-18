# {{ title }}

{{ description }}

## Usage

```sh
dotnet build
dotnet run -- sample.ini                # the whole document as JSON
dotnet run -- sample.ini extra.ini      # merged, later files win
dotnet run -- --get server.port sample.ini
dotnet run -- --section server sample.ini
dotnet run -- --list-sections sample.ini
dotnet run -- --ini sample.ini
```

Sections are ordered as they appear; a repeated key keeps its first position and
takes the last value. `;` and `#` start a comment only at the start of a line or
after whitespace, so URLs keep their fragments. Unknown options exit 2,
unreadable or malformed documents exit 1.
