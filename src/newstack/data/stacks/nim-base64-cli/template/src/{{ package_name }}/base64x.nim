## Base64 in the three flavours a command line tool actually needs: the
## standard alphabet, the URL-safe alphabet, and optional `=` padding.
##
## Pure functions only — nothing here touches argv, stdin or stdout.

import std/[base64, strutils]

type
  Flavour* = enum
    standard, urlSafe

const
  StandardAlphabet* = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  UrlAlphabet* = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

proc withoutPadding*(text: string): string =
  ## Drops trailing `=` characters.
  var stop = text.len
  while stop > 0 and text[stop - 1] == '=':
    dec stop
  text[0 ..< stop]

proc toUrlSafe*(text: string): string =
  ## Standard alphabet to the URL-safe one (RFC 4648 §5) and back, since the
  ## two alphabets differ in exactly two characters.
  text.replace('+', '-').replace('/', '_')

proc fromUrlSafe*(text: string): string =
  text.replace('-', '+').replace('_', '/')

proc encodeBytes*(data: openArray[byte], flavour = standard, padding = true): string =
  ## Encodes raw bytes. `padding = false` strips the trailing `=`.
  result = base64.encode(data)
  if flavour == urlSafe:
    result = toUrlSafe(result)
  if not padding:
    result = withoutPadding(result)

proc encodeText*(text: string, flavour = standard, padding = true): string =
  ## Encodes a string as UTF-8 bytes.
  if text.len == 0:
    return ""
  encodeBytes(text.toOpenArrayByte(0, text.len - 1), flavour, padding)

proc squashWhitespace*(text: string): string =
  ## Base64 in the wild arrives wrapped across lines; drop every space,
  ## tab, CR and LF before decoding.
  for character in text:
    if character notin {' ', '\t', '\r', '\n'}:
      result.add(character)

proc decodeText*(text: string, flavour = standard): string =
  ## Decodes base64 to a string. Raises `ValueError` on malformed input.
  var normalised = squashWhitespace(text)
  if normalised.len > 0 and (normalised.contains('-') or normalised.contains('_')):
    normalised = fromUrlSafe(normalised)
  decode(normalised)
