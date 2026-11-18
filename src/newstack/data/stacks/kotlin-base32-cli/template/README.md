# {{ title }}

{{ description }}

## Usage

```sh
gradle test
gradle run --quiet --args="encode foobar"        # MZXW6YTBOI======
gradle run --quiet --args="decode MZXW6YTBOI======"   # foobar
gradle run --quiet --args="encode --hex" <<< '68656c6c6f'  # NBSWY3DP
```

Encoding always pads to a multiple of eight characters. Decoding accepts
lowercase input, unpadded input and embedded whitespace, but rejects characters
outside the RFC 4648 alphabet, impossible group lengths and non-zero trailing
bits. Bad usage exits 2 and a bad payload exits 1.
