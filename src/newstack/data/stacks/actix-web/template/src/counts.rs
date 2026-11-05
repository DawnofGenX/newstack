//! wc-style counting over the raw UTF-8 bytes of a string.
//!
//! lines  = number of 0x0A bytes
//! words  = maximal runs of bytes not in {0x20,0x09,0x0A,0x0D,0x0B,0x0C}
//! bytes  = length of the UTF-8 encoding

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Counts {
    pub lines: u64,
    pub words: u64,
    pub bytes: u64,
}

#[inline]
pub fn is_word_delim(b: u8) -> bool {
    matches!(b, 0x20 | 0x09 | 0x0A | 0x0D | 0x0B | 0x0C)
}

pub fn count(text: &str) -> Counts {
    let raw = text.as_bytes();
    let mut lines = 0u64;
    let mut words = 0u64;
    let mut in_word = false;
    for &b in raw {
        if b == 0x0A {
            lines += 1;
        }
        if is_word_delim(b) {
            in_word = false;
        } else if !in_word {
            words += 1;
            in_word = true;
        }
    }
    Counts {
        lines,
        words,
        bytes: raw.len() as u64,
    }
}
