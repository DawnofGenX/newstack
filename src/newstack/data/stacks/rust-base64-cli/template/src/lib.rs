const STD: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
const URL: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

pub fn encode(data: &[u8], url_safe: bool, pad: bool) -> String {
    let alpha = if url_safe { URL } else { STD };
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let b0 = chunk[0] as u32;
        let b1 = chunk.get(1).copied().unwrap_or(0) as u32;
        let b2 = chunk.get(2).copied().unwrap_or(0) as u32;
        let n = (b0 << 16) | (b1 << 8) | b2;
        out.push(alpha[(n >> 18) as usize] as char);
        out.push(alpha[((n >> 12) & 63) as usize] as char);
        if chunk.len() > 1 {
            out.push(alpha[((n >> 6) & 63) as usize] as char);
            if chunk.len() > 2 {
                out.push(alpha[(n & 63) as usize] as char);
            } else if pad {
                out.push('=');
            }
        } else if pad {
            out.push_str("==");
        }
    }
    out
}

fn val(c: char, url_safe: bool) -> Option<u8> {
    let std_map = |c: char| -> Option<u8> {
        match c {
            'A'..='Z' => Some(c as u8 - b'A'),
            'a'..='z' => Some(c as u8 - b'a' + 26),
            '0'..='9' => Some(c as u8 - b'0' + 52),
            '+' => Some(62),
            '/' => Some(63),
            _ => None,
        }
    };
    let url_map = |c: char| -> Option<u8> {
        match c {
            'A'..='Z' => Some(c as u8 - b'A'),
            'a'..='z' => Some(c as u8 - b'a' + 26),
            '0'..='9' => Some(c as u8 - b'0' + 52),
            '-' => Some(62),
            '_' => Some(63),
            _ => None,
        }
    };
    if url_safe { url_map(c) } else { std_map(c) }
}

pub fn decode(input: &str, url_safe: bool) -> Result<Vec<u8>, &'static str> {
    let s: String = input.chars().filter(|c| !c.is_whitespace()).collect();
    if s.is_empty() {
        return Ok(Vec::new());
    }
    // pad
    let mut s = s;
    let rem = s.len() % 4;
    if rem != 0 {
        if rem == 1 {
            return Err("bad length");
        }
        s.push_str(&"=".repeat(4 - rem));
    }
    if !s.len().is_multiple_of(4) {
        return Err("bad length");
    }
    let chars: Vec<char> = s.chars().collect();
    if !chars.len().is_multiple_of(4) {
        return Err("bad length");
    }
    let mut out = Vec::with_capacity(chars.len() / 4 * 3);
    for chunk in chars.chunks(4) {
        // count padding
        let pad = chunk.iter().filter(|&&c| c == '=').count();
        if pad > 2 {
            return Err("bad padding");
        }
        // validate padding position
        if pad > 0 && chunk[4 - pad] != '=' {
            return Err("bad padding");
        }
        if pad > 0 {
            for c in &chunk[4 - pad..] {
                if *c != '=' {
                    return Err("bad padding");
                }
            }
            for c in &chunk[..4 - pad] {
                if *c == '=' {
                    return Err("bad padding");
                }
            }
        }
        let v0 = val(chunk[0], url_safe).ok_or("invalid char")?;
        let v1 = val(chunk[1], url_safe).ok_or("invalid char")?;
        let v2 = if chunk[2] == '=' {
            0u8
        } else {
            val(chunk[2], url_safe).ok_or("invalid char")?
        };
        let v3 = if chunk[3] == '=' {
            0u8
        } else {
            val(chunk[3], url_safe).ok_or("invalid char")?
        };
        let n = ((v0 as u32) << 18) | ((v1 as u32) << 12) | ((v2 as u32) << 6) | (v3 as u32);
        out.push((n >> 16) as u8);
        if pad <= 1 {
            out.push(((n >> 8) & 0xff) as u8);
        }
        if pad == 0 {
            out.push((n & 0xff) as u8);
        }
    }
    Ok(out)
}
