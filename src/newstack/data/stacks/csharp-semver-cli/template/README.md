# {{ npm_name }}

{{ description }}

A semantic version reader: parse, order, bump and match ranges (`^`, `~`, `x`,
comparison operators), with the ordering rules from the SemVer 2.0.0
specification, including the prerelease precedence rules.

## Usage

```bash
{{ npm_name }} parse 1.2.3-rc.1
{{ npm_name }} compare 1.0.0-alpha 1.0.0      # prints -1
{{ npm_name }} bump patch 1.2.3               # prints 1.2.4
{{ npm_name }} satisfies 1.4.0 '^1.2.3'       # prints true, exits 0
{{ npm_name }} satisfies 2.0.0 '^1.2.3'       # prints false, exits 1
```

Exit codes: `0` ok or matched, `1` invalid version or unmatched range,
`2` bad usage.

```csharp
var version = SemVersion.Parse("1.2.3-beta.1+build.5");
Console.WriteLine(Ranges.Satisfies(version, "~1.2")); // True
```
