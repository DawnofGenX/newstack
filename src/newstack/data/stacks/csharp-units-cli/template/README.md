# {{ title }}

{{ description }}

## Usage

```sh
dotnet run -- convert 10 km mi
dotnet run -- convert 100 C F
dotnet run -- units temperature
dotnet run -- list
```

`convert` prints the converted value with the target symbol (`6.213712 mi`). Length, mass, volume,
time and data units all carry a factor to their base unit; temperature is affine (C, F, K) and is
handled separately. Crossing dimensions or naming an unknown unit exits 1 with an `error:` line,
a bad command line exits 2 with the usage text.

## Test

```sh
dotnet test
```
