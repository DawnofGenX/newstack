//! CRC-32 (IEEE 802.3) and CRC-32C (Castagnoli) with a shared table-driven core.

const IEEE_POLY: u32 = 0xEDB8_8320;
const CAGNOLI_POLY: u32 = 0x82F6_3B78;

fn build_table(poly: u32) -> [u32; 256] {
    let mut table = [0u32; 256];
    let mut index = 0;
    while index < 256 {
        let mut value = index as u32;
        let mut bit = 0;
        while bit < 8 {
            value = if value & 1 == 1 {
                (value >> 1) ^ poly
            } else {
                value >> 1
            };
            bit += 1;
        }
        table[index] = value;
        index += 1;
    }
    table
}

/// Incremental CRC state: feed byte slices, then call `finish`.
#[derive(Clone)]
pub struct Crc32 {
    table: [u32; 256],
    state: u32,
}

impl Crc32 {
    /// Starts an IEEE 802.3 checksum (the one `zip`, `gzip` and `zlib` use).
    pub fn ieee() -> Self {
        Self::with_poly(IEEE_POLY)
    }

    /// Starts a Castagnoli (CRC-32C) checksum, used by iSCSI and ext4.
    pub fn castagnoli() -> Self {
        Self::with_poly(CAGNOLI_POLY)
    }

    fn with_poly(poly: u32) -> Self {
        Self {
            table: build_table(poly),
            state: 0xFFFF_FFFF,
        }
    }

    /// Feeds more bytes into the checksum.
    pub fn update(&mut self, bytes: &[u8]) -> &mut Self {
        for byte in bytes {
            let index = ((self.state ^ u32::from(*byte)) & 0xFF) as usize;
            self.state = (self.state >> 8) ^ self.table[index];
        }
        self
    }

    /// Returns the final checksum; calling it twice is safe.
    pub fn finish(&self) -> u32 {
        self.state ^ 0xFFFF_FFFF
    }
}

/// One-shot CRC-32 (IEEE 802.3).
pub fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = Crc32::ieee();
    crc.update(bytes);
    crc.finish()
}

/// One-shot CRC-32C (Castagnoli).
pub fn crc32c(bytes: &[u8]) -> u32 {
    let mut crc = Crc32::castagnoli();
    crc.update(bytes);
    crc.finish()
}

/// Lowercase zero padded hex, the form `crc32` tools print.
pub fn to_hex(value: u32) -> String {
    format!("{value:08x}")
}
