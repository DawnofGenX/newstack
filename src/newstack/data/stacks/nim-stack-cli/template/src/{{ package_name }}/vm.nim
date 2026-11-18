## A small integer stack machine: one token in, one stack operation out.
##
## The point is the error messages: a stack language that silently wraps around
## or hands back garbage on underflow teaches nothing, so every failure names the
## word and the depth it found.

import std/strutils

type
  VmError* = object of CatchableError
    ## Raised for anything the user could have typed wrong: an unknown word, a
    ## number int64 cannot hold, too few values, or a division by zero.
  Vm* = object
    ## The machine. `stack` is bottom-first, exactly as it is printed.
    stack*: seq[int64]

proc newVm*(): Vm =
  ## An empty machine.
  Vm(stack: @[])

proc depth*(vm: Vm): int =
  ## How many values are on the stack.
  vm.stack.len

proc push*(vm: var Vm, value: int64) =
  ## Pushes one value.
  vm.stack.add(value)

proc `$`*(vm: Vm): string =
  ## The stack rendered bottom-first, space separated; empty stays empty.
  var parts: seq[string]
  for value in vm.stack:
    parts.add($value)
  parts.join(" ")

proc popOne(vm: var Vm, word: string): int64 =
  if vm.stack.len < 1:
    raise newException(VmError, "stack underflow: '" & word &
      "' needs one value, have 0")
  vm.stack.pop()

proc popTwo(vm: var Vm, word: string): tuple[a, b: int64] =
  if vm.stack.len < 2:
    raise newException(VmError, "stack underflow: '" & word &
      "' needs two values, have " & $vm.stack.len)
  let b = vm.stack.pop()
  let a = vm.stack.pop()
  (a: a, b: b)

proc parseNumber(word: string): int64 =
  ## `parseBiggestInt` accepts a leading sign, so negative numbers are ordinary
  ## values rather than options.
  try:
    int64(parseBiggestInt(word))
  except ValueError:
    raise newException(VmError, "not a number or command: '" & word & "'")

proc step*(vm: var Vm, word: string) =
  ## Applies one word. Raises `VmError` on anything that does not fit.
  case word
  of "+":
    let operands = popTwo(vm, word)
    vm.stack.add(operands.a + operands.b)
  of "-":
    let operands = popTwo(vm, word)
    vm.stack.add(operands.a - operands.b)
  of "*":
    let operands = popTwo(vm, word)
    vm.stack.add(operands.a * operands.b)
  of "/":
    let operands = popTwo(vm, word)
    if operands.b == 0:
      raise newException(VmError, "division by zero")
    vm.stack.add(operands.a div operands.b)
  of "%":
    let operands = popTwo(vm, word)
    if operands.b == 0:
      raise newException(VmError, "division by zero")
    vm.stack.add(operands.a mod operands.b)
  of "dup":
    let value = popOne(vm, word)
    vm.stack.add(value)
    vm.stack.add(value)
  of "swap":
    let operands = popTwo(vm, word)
    vm.stack.add(operands.b)
    vm.stack.add(operands.a)
  of "drop":
    discard popOne(vm, word)
  of "abs":
    let value = popOne(vm, word)
    if value == low(int64):
      raise newException(VmError, "abs would overflow: " & $value)
    vm.stack.add(if value < 0: -value else: value)
  of "neg":
    let value = popOne(vm, word)
    vm.stack.add(-value)
  of "min":
    let operands = popTwo(vm, word)
    vm.stack.add(if operands.a < operands.b: operands.a else: operands.b)
  of "max":
    let operands = popTwo(vm, word)
    vm.stack.add(if operands.a > operands.b: operands.a else: operands.b)
  of "depth":
    vm.stack.add(int64(vm.stack.len))
  else:
    vm.stack.add(parseNumber(word))

proc eval*(vm: var Vm, words: seq[string]) =
  ## Runs every word in order. The first failure aborts, leaving the stack as it
  ## was after the last good word — what a REPL would show you.
  for word in words:
    if word.len == 0:
      continue
    step(vm, word)
