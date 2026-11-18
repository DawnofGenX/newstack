/** IPv4 CIDR arithmetic: masks, ranges, containment and overlap. */
export interface Cidr {
  /** The text the block was parsed from. */
  text: string;
  /** The network address as a 32 bit unsigned integer. */
  network: number;
  /** The prefix length, 0..32. */
  prefix: number;
  /** The last address in the block. */
  broadcast: number;
  /** The netmask as a 32 bit unsigned integer. */
  mask: number;
  /** How many addresses the block holds. */
  size: number;
}

/** Thrown when a CIDR block or address cannot be parsed. */
export class CidrError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CidrError";
  }
}

/** Parses dotted quad notation into an unsigned 32 bit integer. */
export function ipToInt(text: string): number {
  const parts = text.split(".");
  if (parts.length !== 4) {
    throw new CidrError(`expected four dotted octets, got '${text}'`);
  }
  let value = 0;
  for (const part of parts) {
    if (!/^\d{1,3}$/.test(part)) {
      throw new CidrError(`octet '${part}' is not a number`);
    }
    const octet = Number(part);
    if (octet > 255) {
      throw new CidrError(`octet ${octet} is out of range 0-255`);
    }
    value = value * 256 + octet;
  }
  return value >>> 0;
}

/** Formats an unsigned 32 bit integer as dotted quad notation. */
export function intToIp(value: number): string {
  const octets = [value >>> 24, (value >>> 16) & 255, (value >>> 8) & 255, value & 255];
  return octets.join(".");
}

function maskFor(prefix: number): number {
  if (prefix === 0) {
    return 0;
  }
  return (0xffffffff << (32 - prefix)) >>> 0;
}

/** Parses `address/prefix`, clearing any bits of the host part. */
export function parseCidr(text: string): Cidr {
  const trimmed = text.trim();
  const pieces = trimmed.split("/");
  if (pieces.length !== 2) {
    throw new CidrError(`expected address/prefix, got '${trimmed}'`);
  }
  const [addressText, prefixText] = pieces;
  if (!/^\d{1,2}$/.test(prefixText)) {
    throw new CidrError(`prefix '${prefixText}' is not a number`);
  }
  const prefix = Number(prefixText);
  if (prefix > 32) {
    throw new CidrError(`prefix ${prefix} is out of range 0-32`);
  }
  const address = ipToInt(addressText);
  const mask = maskFor(prefix);
  const network = (address & mask) >>> 0;
  const broadcast = (network | (~mask >>> 0)) >>> 0;
  return {
    text: trimmed,
    network,
    prefix,
    broadcast,
    mask,
    size: 2 ** (32 - prefix),
  };
}

/** Returns whether `address` falls inside `block`. */
export function contains(block: Cidr, address: string): boolean {
  return ((ipToInt(address) & block.mask) >>> 0) === block.network;
}

/** Returns whether two blocks share at least one address. */
export function overlaps(left: Cidr, right: Cidr): boolean {
  return left.network <= right.broadcast && right.network <= left.broadcast;
}

/** The canonical form of a block: network address plus prefix. */
export function normalize(text: string): string {
  const block = parseCidr(text);
  return `${intToIp(block.network)}/${block.prefix}`;
}

/** Usable host count: /31 and /32 are special cases in RFC 3021. */
export function hostCount(block: Cidr): number {
  return block.prefix >= 31 ? block.size : block.size - 2;
}

/** A one line summary used by the CLI table output. */
export function describe(block: Cidr): string {
  return `${intToIp(block.network)}/${block.prefix}` +
    ` network=${intToIp(block.network)}` +
    ` broadcast=${intToIp(block.broadcast)}` +
    ` hosts=${hostCount(block)}`;
}
