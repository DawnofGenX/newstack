import { assertEquals, assertThrows } from "./asserts.ts";

import {
  CidrError,
  contains,
  describe,
  hostCount,
  intToIp,
  ipToInt,
  normalize,
  overlaps,
  parseCidr,
} from "../src/cidr.ts";

Deno.test("ipToInt and intToIp round trip", () => {
  for (const text of ["0.0.0.0", "10.0.0.1", "192.168.1.254", "255.255.255.255"]) {
    assertEquals(intToIp(ipToInt(text)), text);
  }
});

Deno.test("ipToInt rejects bad input", () => {
  assertThrows(() => ipToInt("10.0.0"), CidrError);
  assertThrows(() => ipToInt("10.0.0.256"), CidrError);
  assertThrows(() => ipToInt("10.0.0.x"), CidrError);
});

Deno.test("parseCidr clears host bits", () => {
  const block = parseCidr("10.1.2.3/8");
  assertEquals(intToIp(block.network), "10.0.0.0");
  assertEquals(intToIp(block.broadcast), "10.255.255.255");
  assertEquals(block.size, 16777216);
  assertEquals(hostCount(block), 16777214);
});

Deno.test("a /32 block holds one address", () => {
  const block = parseCidr("192.168.1.7/32");
  assertEquals(block.size, 1);
  assertEquals(hostCount(block), 1);
  assertEquals(contains(block, "192.168.1.7"), true);
  assertEquals(contains(block, "192.168.1.8"), false);
});

Deno.test("a /0 block spans the whole space", () => {
  const block = parseCidr("0.0.0.0/0");
  assertEquals(intToIp(block.broadcast), "255.255.255.255");
  assertEquals(contains(block, "8.8.8.8"), true);
});

Deno.test("prefixes out of range are refused", () => {
  assertThrows(() => parseCidr("10.0.0.0/33"), CidrError);
  assertThrows(() => parseCidr("10.0.0.0"), CidrError);
  assertThrows(() => parseCidr("10.0.0.0/x"), CidrError);
});

Deno.test("overlaps is symmetric", () => {
  const big = parseCidr("10.0.0.0/8");
  const small = parseCidr("10.1.0.0/16");
  const other = parseCidr("11.0.0.0/8");
  assertEquals(overlaps(big, small), true);
  assertEquals(overlaps(small, big), true);
  assertEquals(overlaps(big, other), false);
});

Deno.test("normalize returns the canonical form", () => {
  assertEquals(normalize("10.1.2.3/8"), "10.0.0.0/8");
  assertEquals(normalize("  192.168.0.5/24 "), "192.168.0.0/24");
});

Deno.test("describe mentions network, broadcast and host count", () => {
  assertEquals(
    describe(parseCidr("192.168.4.9/30")),
    "192.168.4.8/30 network=192.168.4.8 broadcast=192.168.4.11 hosts=2",
  );
});
