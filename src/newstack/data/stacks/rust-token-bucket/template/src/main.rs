use std::process::ExitCode;

fn arg_value(args: &[String], flag: &str) -> Option<String> {
    let mut iter = args.iter();
    while let Some(item) = iter.next() {
        if item == flag {
            return iter.next().cloned();
        }
    }
    None
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let capacity = arg_value(&args, "--capacity")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(5);
    let rate = arg_value(&args, "--rate")
        .and_then(|v| v.parse::<f64>().ok())
        .unwrap_or(1.0);
    let requests = arg_value(&args, "--requests")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(8);
    let interval_ms = arg_value(&args, "--interval-ms")
        .and_then(|v| v.parse::<u64>().ok())
        .unwrap_or(400);

    let mut bucket = {{ package_name }}::TokenBucket::new(capacity, rate, 0);
    println!("capacity={capacity} rate={rate}/s interval={interval_ms}ms");
    for i in 0..requests {
        let now = i * interval_ms;
        let allowed = bucket.try_acquire(now);
        println!(
            "request {n}: t={now}ms {} remaining={}",
            if allowed { "allow" } else { "deny" },
            bucket.available(now),
            n = i + 1
        );
    }
    ExitCode::SUCCESS
}
