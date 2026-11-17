use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};
use std::fmt;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default)]
    pub debug: bool,
    #[serde(default = "default_name")]
    pub name: String,
}

fn default_host() -> String {
    "127.0.0.1".to_string()
}
fn default_port() -> u16 {
    8080
}
fn default_name() -> String {
    "app".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            host: default_host(),
            port: default_port(),
            debug: false,
            name: default_name(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConfigError {
    pub file: Option<PathBuf>,
    pub key: Option<String>,
    pub message: String,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match (&self.file, &self.key) {
            (Some(file), Some(key)) => {
                write!(f, "{}: key {:?}: {}", file.display(), key, self.message)
            }
            (Some(file), None) => write!(f, "{}: {}", file.display(), self.message),
            (None, Some(key)) => write!(f, "key {:?}: {}", key, self.message),
            (None, None) => write!(f, "{}", self.message),
        }
    }
}

impl std::error::Error for ConfigError {}

#[derive(Debug, Clone, Default)]
pub struct CliOverrides {
    pub config: Option<PathBuf>,
    pub env_file: Option<PathBuf>,
    pub host: Option<String>,
    pub port: Option<String>,
    pub debug_set: bool,
    pub name: Option<String>,
    pub explain: bool,
}

pub fn parse_dotenv(input: &str) -> HashMap<String, String> {
    let mut out = HashMap::new();
    for raw in input.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let line = line.strip_prefix("export ").unwrap_or(line).trim();
        let Some((k, v)) = line.split_once('=') else {
            continue;
        };
        let key = k.trim();
        if key.is_empty() {
            continue;
        }
        out.insert(key.to_string(), unquote(v.trim()));
    }
    out
}

fn unquote(s: &str) -> String {
    if s.len() >= 2
        && ((s.starts_with('"') && s.ends_with('"')) || (s.starts_with('\'') && s.ends_with('\'')))
    {
        s[1..s.len() - 1].to_string()
    } else {
        s.to_string()
    }
}

#[derive(Debug, Clone)]
pub struct Layers {
    pub config: Config,
    pub provenance: BTreeMap<String, &'static str>,
}

pub fn resolve(cli: &CliOverrides, env: &HashMap<String, String>) -> Result<Layers, ConfigError> {
    let mut cfg = Config::default();
    let mut provenance: BTreeMap<String, &'static str> = BTreeMap::new();
    for key in ["host", "port", "debug", "name"] {
        provenance.insert(key.to_string(), "defaults");
    }

    // File layer.
    let file_value: Option<serde_json::Value> = match &cli.config {
        Some(path) => {
            let text = std::fs::read_to_string(path).map_err(|e| ConfigError {
                file: Some(path.to_path_buf()),
                key: None,
                message: e.to_string(),
            })?;
            let value: serde_json::Value =
                serde_json::from_str(&text).map_err(|e| ConfigError {
                    file: Some(path.to_path_buf()),
                    key: None,
                    message: e.to_string(),
                })?;
            Some(value)
        }
        None => None,
    };

    if let Some(value) = &file_value {
        let path = cli.config.as_ref().unwrap();
        apply_file(&mut cfg, &mut provenance, value, path)?;
    }

    // Env layer. Keys: APP_HOST, APP_PORT, APP_DEBUG, APP_NAME.
    if let Some(v) = env.get("APP_HOST") {
        cfg.host = v.clone();
        provenance.insert("host".to_string(), "env");
    }
    if let Some(v) = env.get("APP_PORT") {
        let parsed: u16 = v.parse().map_err(|_| ConfigError {
            file: None,
            key: Some("port".to_string()),
            message: format!("invalid port {:?}", v),
        })?;
        cfg.port = parsed;
        provenance.insert("port".to_string(), "env");
    }
    if let Some(v) = env.get("APP_DEBUG") {
        let parsed: bool = v.parse().map_err(|_| ConfigError {
            file: None,
            key: Some("debug".to_string()),
            message: format!("invalid bool {:?}", v),
        })?;
        cfg.debug = parsed;
        provenance.insert("debug".to_string(), "env");
    }
    if let Some(v) = env.get("APP_NAME") {
        cfg.name = v.clone();
        provenance.insert("name".to_string(), "env");
    }

    // CLI layer.
    if let Some(v) = &cli.host {
        cfg.host = v.clone();
        provenance.insert("host".to_string(), "cli");
    }
    if let Some(v) = &cli.port {
        let parsed: u16 = v.parse().map_err(|_| ConfigError {
            file: None,
            key: Some("port".to_string()),
            message: format!("invalid port {:?}", v),
        })?;
        cfg.port = parsed;
        provenance.insert("port".to_string(), "cli");
    }
    if cli.debug_set {
        cfg.debug = true;
        provenance.insert("debug".to_string(), "cli");
    }
    if let Some(v) = &cli.name {
        cfg.name = v.clone();
        provenance.insert("name".to_string(), "cli");
    }

    Ok(Layers {
        config: cfg,
        provenance,
    })
}

fn apply_file(
    cfg: &mut Config,
    provenance: &mut BTreeMap<String, &'static str>,
    value: &serde_json::Value,
    path: &std::path::Path,
) -> Result<(), ConfigError> {
    let obj = value.as_object().ok_or_else(|| ConfigError {
        file: Some(path.to_path_buf()),
        key: None,
        message: "expected JSON object".to_string(),
    })?;
    if let Some(v) = obj.get("host") {
        let s = v.as_str().ok_or_else(|| ConfigError {
            file: Some(path.to_path_buf()),
            key: Some("host".to_string()),
            message: "expected string".to_string(),
        })?;
        cfg.host = s.to_string();
        provenance.insert("host".to_string(), "file");
    }
    if let Some(v) = obj.get("port") {
        let n = v.as_u64().ok_or_else(|| ConfigError {
            file: Some(path.to_path_buf()),
            key: Some("port".to_string()),
            message: "expected integer".to_string(),
        })?;
        if n > u16::MAX as u64 {
            return Err(ConfigError {
                file: Some(path.to_path_buf()),
                key: Some("port".to_string()),
                message: "out of range".to_string(),
            });
        }
        cfg.port = n as u16;
        provenance.insert("port".to_string(), "file");
    }
    if let Some(v) = obj.get("debug") {
        let b = v.as_bool().ok_or_else(|| ConfigError {
            file: Some(path.to_path_buf()),
            key: Some("debug".to_string()),
            message: "expected bool".to_string(),
        })?;
        cfg.debug = b;
        provenance.insert("debug".to_string(), "file");
    }
    if let Some(v) = obj.get("name") {
        let s = v.as_str().ok_or_else(|| ConfigError {
            file: Some(path.to_path_buf()),
            key: Some("name".to_string()),
            message: "expected string".to_string(),
        })?;
        cfg.name = s.to_string();
        provenance.insert("name".to_string(), "file");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn precedence_cli_wins() {
        let dir = std::env::temp_dir();
        let path = dir.join("cfg.json");
        std::fs::write(
            &path,
            r#"{"host":"filehost","port":9090,"debug":false,"name":"fileapp"}"#,
        )
        .unwrap();
        let mut env = HashMap::new();
        env.insert("APP_PORT".to_string(), "7070".to_string());
        env.insert("APP_DEBUG".to_string(), "true".to_string());
        let cli = CliOverrides {
            config: Some(path.to_path_buf()),
            host: None,
            port: Some("1111".to_string()),
            debug_set: false,
            name: None,
            env_file: None,
            explain: false,
        };
        let layers = resolve(&cli, &env).unwrap();
        assert_eq!(layers.config.host, "filehost");
        assert_eq!(layers.config.port, 1111);
        assert!(layers.config.debug);
        assert_eq!(layers.config.name, "fileapp");
        assert_eq!(layers.provenance.get("port").unwrap(), &"cli");
        assert_eq!(layers.provenance.get("debug").unwrap(), &"env");
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn error_names_file_and_key() {
        let dir = std::env::temp_dir();
        let path = dir.join("bad.json");
        std::fs::write(&path, r#"{"port":"nope"}"#).unwrap();
        let cli = CliOverrides {
            config: Some(path.to_path_buf()),
            ..Default::default()
        };
        let err = resolve(&cli, &HashMap::new()).unwrap_err();
        let msg = err.to_string();
        assert!(msg.contains("bad.json"), "{}", msg);
        assert!(msg.contains("port"), "{}", msg);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn dotenv_parser() {
        let input = "# comment\nFOO=bar\nexport BAZ=\"qux\"\nEMPTY=\nQUOTED='a b'\n";
        let m = parse_dotenv(input);
        assert_eq!(m.get("FOO").unwrap(), "bar");
        assert_eq!(m.get("BAZ").unwrap(), "qux");
        assert_eq!(m.get("EMPTY").unwrap(), "");
        assert_eq!(m.get("QUOTED").unwrap(), "a b");
    }
}
