use std::fs;
use tempfile::tempdir;

#[test]
fn root_fixed_fixture() {
    let d = tempdir().unwrap();
    let a = d.path().join("a.txt");
    let b = d.path().join("b.txt");
    let c = d.path().join("c.txt");
    fs::write(&a, b"alpha\n").unwrap();
    fs::write(&b, b"beta\n").unwrap();
    fs::write(&c, b"gamma\n").unwrap();
    let leaves = vec![
        {{ package_name }}::hash_file(a.to_str().unwrap()).unwrap(),
        {{ package_name }}::hash_file(b.to_str().unwrap()).unwrap(),
        {{ package_name }}::hash_file(c.to_str().unwrap()).unwrap(),
    ];
    let root = {{ package_name }}::merkle_root(&leaves);
    assert_eq!(
        {{ package_name }}::hex(&root),
        "010672548ce4079077c5a049f1020c85dea8fbddd12267cca106bc55aff44ebe"
    );
}

#[test]
fn proof_verifies() {
    let d = tempdir().unwrap();
    let a = d.path().join("a.txt");
    let b = d.path().join("b.txt");
    fs::write(&a, b"alpha\n").unwrap();
    fs::write(&b, b"beta\n").unwrap();
    let leaves = vec![
        {{ package_name }}::hash_file(a.to_str().unwrap()).unwrap(),
        {{ package_name }}::hash_file(b.to_str().unwrap()).unwrap(),
    ];
    let proof = {{ package_name }}::generate_proof(&leaves, 0).unwrap();
    assert!({{ package_name }}::verify_proof(leaves[0], &proof));
    // tampered leaf fails
    let mut bad = leaves[0];
    bad[0] ^= 1;
    assert!(!{{ package_name }}::verify_proof(bad, &proof));
}

#[test]
fn empty_tree_root() {
    let r = {{ package_name }}::merkle_root(&[]);
    assert_eq!({{ package_name }}::hex(&r).len(), 64);
}
