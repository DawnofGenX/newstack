# {{ title }}

{{ description }}

## Usage

```rust
use {{ package_name }}::LruCache;
let mut cache = LruCache::new(128);
cache.put("key", "value");
assert_eq!(cache.get(&"key"), Some(&"value"));
```

## Test

```sh
cargo test
```
