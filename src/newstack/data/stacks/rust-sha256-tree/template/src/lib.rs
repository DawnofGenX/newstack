use sha2::{Digest, Sha256};
use std::fs;
use std::io;

pub type Hash = [u8; 32];

pub fn sha256(data: &[u8]) -> Hash {
    let mut h = Sha256::new();
    h.update(data);
    h.finalize().into()
}

pub fn hash_file(path: &str) -> io::Result<Hash> {
    let data = fs::read(path)?;
    Ok(sha256(&data))
}

pub fn merkle_root(leaves: &[Hash]) -> Hash {
    if leaves.is_empty() {
        return sha256(b"");
    }
    let mut level: Vec<Hash> = leaves.to_vec();
    while level.len() > 1 {
        let mut next: Vec<Hash> = Vec::with_capacity(level.len().div_ceil(2));
        let mut i = 0;
        while i < level.len() {
            let left = level[i];
            let right = if i + 1 < level.len() {
                level[i + 1]
            } else {
                level[i]
            };
            let mut h = Sha256::new();
            h.update(left);
            h.update(right);
            next.push(h.finalize().into());
            i += 2;
        }
        level = next;
    }
    level[0]
}

#[derive(Clone, Debug)]
pub struct Proof {
    pub index: usize,
    pub siblings: Vec<Hash>,
    pub root: Hash,
}

pub fn generate_proof(leaves: &[Hash], index: usize) -> Option<Proof> {
    if index >= leaves.len() || leaves.is_empty() {
        return None;
    }
    let mut siblings = Vec::new();
    let mut level: Vec<Hash> = leaves.to_vec();
    let mut idx = index;
    while level.len() > 1 {
        let sibling_idx = if idx.is_multiple_of(2) {
            if idx + 1 < level.len() { idx + 1 } else { idx }
        } else {
            idx - 1
        };
        siblings.push(level[sibling_idx]);
        // build next level
        let mut next: Vec<Hash> = Vec::with_capacity(level.len().div_ceil(2));
        let mut i = 0;
        while i < level.len() {
            let left = level[i];
            let right = if i + 1 < level.len() {
                level[i + 1]
            } else {
                level[i]
            };
            let mut h = Sha256::new();
            h.update(left);
            h.update(right);
            next.push(h.finalize().into());
            i += 2;
        }
        level = next;
        idx /= 2;
    }
    Some(Proof {
        index,
        siblings,
        root: if level.is_empty() {
            sha256(b"")
        } else {
            level[0]
        },
    })
}

pub fn verify_proof(leaf: Hash, proof: &Proof) -> bool {
    let mut cur = leaf;
    let mut idx = proof.index;
    for sib in &proof.siblings {
        let mut h = Sha256::new();
        if idx.is_multiple_of(2) {
            // if last duplicated, sibling == cur; still hash cur||sib
            h.update(cur);
            h.update(sib);
        } else {
            h.update(sib);
            h.update(cur);
        }
        cur = h.finalize().into();
        idx /= 2;
    }
    cur == proof.root
}

pub fn hex(h: &Hash) -> String {
    h.iter().map(|b| format!("{b:02x}")).collect()
}
