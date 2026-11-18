#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Op {
    Set(u32),
    Clear(u32),
    Toggle(u32),
}

pub fn parse_value(s: &str) -> Result<u32, String> {
    let s = s.trim();
    if let Some(rest) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        u32::from_str_radix(rest, 16).map_err(|e| e.to_string())
    } else {
        s.parse::<u32>().map_err(|e| e.to_string())
    }
}

pub fn apply(value: u32, ops: &[Op]) -> u32 {
    let mut v = value;
    for op in ops {
        match op {
            Op::Set(b) => v |= 1u32 << b,
            Op::Clear(b) => v &= !(1u32 << b),
            Op::Toggle(b) => v ^= 1u32 << b,
        }
    }
    v
}

pub fn format_result(value: u32) -> String {
    format!("{} 0x{:x} 0b{:b}", value, value, value)
}

pub fn list_bits(value: u32) -> Vec<u32> {
    (0..32).filter(|i| value & (1 << i) != 0).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_hex() {
        assert_eq!(parse_value("0xff").unwrap(), 255);
    }

    #[test]
    fn parse_dec() {
        assert_eq!(parse_value("42").unwrap(), 42);
    }

    #[test]
    fn set_clear_toggle() {
        let v = apply(0, &[Op::Set(3), Op::Set(0)]);
        assert_eq!(v, 0b1001);
        let v = apply(v, &[Op::Clear(0)]);
        assert_eq!(v, 0b1000);
        let v = apply(v, &[Op::Toggle(3)]);
        assert_eq!(v, 0);
    }

    #[test]
    fn list_bits_works() {
        assert_eq!(list_bits(0b1010), vec![1, 3]);
    }
}
