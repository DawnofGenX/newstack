use std::process;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut proof_target: Option<String> = None;
    let mut files: Vec<String> = Vec::new();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--proof" => {
                if i + 1 >= args.len() {
                    eprintln!("missing file after --proof");
                    process::exit(2);
                }
                proof_target = Some(args[i + 1].clone());
                i += 2;
                continue;
            }
            a => files.push(a.to_string()),
        }
        i += 1;
    }

    if files.is_empty() {
        eprintln!("usage: sha [--proof <file>] <files...>");
        process::exit(2);
    }

    let mut leaves = Vec::new();
    for f in &files {
        match {{ package_name }}::hash_file(f) {
            Ok(h) => leaves.push(h),
            Err(e) => {
                eprintln!("{}: {}", f, e);
                process::exit(1);
            }
        }
    }

    let root = {{ package_name }}::merkle_root(&leaves);
    println!("{}", {{ package_name }}::hex(&root));

    if let Some(target) = proof_target {
        // find index of target in files
        let idx = match files.iter().position(|f| f == &target) {
            Some(i) => i,
            None => {
                eprintln!("proof target not in file list");
                process::exit(2);
            }
        };
        match {{ package_name }}::generate_proof(&leaves, idx) {
            Some(proof) => {
                if {{ package_name }}::verify_proof(leaves[idx], &proof) {
                    println!("verified: {}", target);
                } else {
                    eprintln!("proof verification failed");
                    process::exit(1);
                }
            }
            None => {
                eprintln!("could not generate proof");
                process::exit(1);
            }
        }
    }
}
