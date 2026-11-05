//! Persistence: one SQLite file, a connection pool, sqlx's embedded migrator.
//!
//! The migration set is EMBEDDED at compile time (`sqlx::migrate!`), so the
//! shipped binary can never drift from its schema and needs no migrations
//! directory at runtime.

use sqlx::sqlite::{SqliteConnectOptions, SqliteJournalMode, SqlitePoolOptions};
use sqlx::{Row, SqlitePool};
use std::str::FromStr;

/// One stored note. Field order is the wire key order (serde emits in
/// declaration order, unlike `serde_json::Value`'s map).
#[derive(Debug, Clone, serde::Serialize, PartialEq, Eq)]
pub struct Note {
    pub id: i64,
    pub title: String,
    pub body: String,
    pub created_at: String,
}

#[derive(Clone)]
pub struct Store {
    pool: SqlitePool,
}

#[derive(Debug)]
pub enum StoreError {
    NotFound(i64),
    Db(sqlx::Error),
}

impl From<sqlx::Error> for StoreError {
    fn from(value: sqlx::Error) -> Self {
        StoreError::Db(value)
    }
}

/// `now()` in the same shape SQLite writes: second precision, UTC, trailing Z.
pub fn now_stamp() -> String {
    // `SystemTime` avoids pulling a chrono dependency; SQLite stores whatever
    // string we hand it and sorts it lexicographically.
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    format_unix(secs)
}

/// Split out so the self-checks can assert the exact wire shape.
pub fn format_unix(secs: u64) -> String {
    let days = (secs / 86_400) as i64;
    let rem = secs % 86_400;
    let (y, m, d) = civil_from_days(days);
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        y,
        m,
        d,
        rem / 3600,
        (rem % 3600) / 60,
        rem % 60
    )
}

/// Howard Hinnant's days-from-civil, inverted. No leap-second cleverness: the
/// stamps we write are for ordering, not astronomy.
pub fn civil_from_days(z: i64) -> (i64, u32, u32) {
    let z = z + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = (z - era * 146_097) as u64;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}

impl Store {
    /// Open (creating if needed) the database at `path` and apply migrations.
    pub async fn open(path: &str) -> Result<Self, sqlx::Error> {
        let options = SqliteConnectOptions::from_str(path)?
            .create_if_missing(true)
            .journal_mode(SqliteJournalMode::Wal)
            .busy_timeout(std::time::Duration::from_secs(5))
            .foreign_keys(true);
        let pool = SqlitePoolOptions::new()
            .max_connections(4)
            .connect_with(options)
            .await?;
        sqlx::migrate!("./migrations").run(&pool).await?;
        Ok(Store { pool })
    }

    pub async fn count(&self) -> Result<i64, sqlx::Error> {
        let row = sqlx::query("SELECT COUNT(*) AS n FROM notes")
            .fetch_one(&self.pool)
            .await?;
        Ok(row.get::<i64, _>("n"))
    }

    pub async fn create(&self, title: &str, body: &str) -> Result<Note, sqlx::Error> {
        let stamp = now_stamp();
        let row = sqlx::query(
            "INSERT INTO notes (title, body, created_at, updated_at) VALUES (?, ?, ?, ?) \
             RETURNING id, title, body, created_at",
        )
        .bind(title)
        .bind(body)
        .bind(&stamp)
        .bind(&stamp)
        .fetch_one(&self.pool)
        .await?;
        Ok(note_from_row(&row))
    }

    pub async fn list(&self) -> Result<Vec<Note>, sqlx::Error> {
        let rows = sqlx::query("SELECT id, title, body, created_at FROM notes ORDER BY id")
            .fetch_all(&self.pool)
            .await?;
        Ok(rows.iter().map(note_from_row).collect())
    }

    pub async fn get(&self, id: i64) -> Result<Note, StoreError> {
        match sqlx::query("SELECT id, title, body, created_at FROM notes WHERE id = ?")
            .bind(id)
            .fetch_optional(&self.pool)
            .await?
        {
            Some(row) => Ok(note_from_row(&row)),
            None => Err(StoreError::NotFound(id)),
        }
    }

    /// Fields left `None` keep their stored value; `created_at` never moves.
    pub async fn patch(
        &self,
        id: i64,
        title: Option<&str>,
        body: Option<&str>,
    ) -> Result<Note, StoreError> {
        let current = self.get(id).await?;
        let next_title = title.unwrap_or(&current.title);
        let next_body = body.unwrap_or(&current.body);
        let row = sqlx::query(
            "UPDATE notes SET title = ?, body = ?, updated_at = ? WHERE id = ? \
             RETURNING id, title, body, created_at",
        )
        .bind(next_title)
        .bind(next_body)
        .bind(now_stamp())
        .bind(id)
        .fetch_one(&self.pool)
        .await?;
        Ok(note_from_row(&row))
    }

    /// `rows_affected == 0` is the 404 signal — `DELETE` on a missing row is not
    /// an error in SQL, so the affected count is the only evidence.
    pub async fn delete(&self, id: i64) -> Result<(), StoreError> {
        let done = sqlx::query("DELETE FROM notes WHERE id = ?")
            .bind(id)
            .execute(&self.pool)
            .await?;
        if done.rows_affected() == 0 {
            return Err(StoreError::NotFound(id));
        }
        Ok(())
    }
}

fn note_from_row(row: &sqlx::sqlite::SqliteRow) -> Note {
    Note {
        id: row.get::<i64, _>("id"),
        title: row.get::<String, _>("title"),
        body: row.get::<String, _>("body"),
        created_at: row.get::<String, _>("created_at"),
    }
}

/// Trim + reject blanks. Kept separate from the handler so the self-checks can
/// pin the rule without a socket.
pub fn normalise_title(raw: &str) -> Option<String> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}
