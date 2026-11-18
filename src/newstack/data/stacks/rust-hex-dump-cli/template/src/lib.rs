pub fn hex_dump(data: &[u8], width: usize) -> String {
    let width = if width == 0 { 16 } else { width };
    let mut out = String::new();
    let mut offset = 0;
    while offset < data.len() {
        let chunk = &data[offset..(offset + width).min(data.len())];
        out.push_str(&format!("{:08x}  ", offset));
        // hex bytes
        for i in 0..width {
            if i < chunk.len() {
                out.push_str(&format!("{:02x} ", chunk[i]));
            } else {
                out.push_str("   ");
            }
            if i == 7 {
                out.push(' ');
            }
        }
        out.push(' ');
        for b in chunk {
            if b.is_ascii_graphic() || *b == b' ' {
                out.push(*b as char);
            } else {
                out.push('.');
            }
        }
        out.push('\n');
        offset += width;
    }
    if data.is_empty() {
        // print nothing? keep empty
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_input() {
        assert_eq!(hex_dump(&[], 16), "");
    }

    #[test]
    fn single_line() {
        let out = hex_dump(b"abc", 16);
        assert!(out.starts_with("00000000  "));
        assert!(out.contains("61 62 63"));
        assert!(out.contains("abc"));
    }

    #[test]
    fn offset_second_line() {
        let data = vec![0u8; 20];
        let out = hex_dump(&data, 16);
        let lines: Vec<&str> = out.lines().collect();
        assert_eq!(lines.len(), 2);
        assert!(lines[1].starts_with("00000010"));
    }

    #[test]
    fn nonprintable_becomes_dot() {
        let out = hex_dump(&[0x01, 0x41], 16);
        assert!(out.contains(".A"));
    }
}
