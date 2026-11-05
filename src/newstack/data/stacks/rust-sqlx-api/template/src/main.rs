//! Notes service entry point: `--selftest` runs the offline suite, otherwise
//! serve. `DB_PATH` and `PORT` are the only knobs.

use {{ package_name }}::{selftest, store::Store};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--selftest") {
        let n = selftest::run();
        println!("selftest: {n} checks passed");
        return;
    }
    if let Err(err) = real_main() {
        eprintln!("fatal: {err}");
        std::process::exit(1);
    }
}

fn real_main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = std::env::var("DB_PATH").unwrap_or_else(|_| "notes.db".to_string());
    let port = std::env::var("PORT").unwrap_or_else(|_| "5470".to_string());
    let port: u16 = match port.parse() {
        Ok(port) => port,
        Err(_) => {
            eprintln!("PORT must be a number, got {port:?}");
            std::process::exit(2);
        }
    };
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?;
    runtime.block_on(async move {
        let store = Store::open(&db_path).await?;
        let addr = format!("127.0.0.1:{port}");
        {{ package_name }}::run(store, &addr).await?;
        Ok::<(), Box<dyn std::error::Error>>(())
    })?;
    Ok(())
}
