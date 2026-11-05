//! Integration tests against a real SQLite file in a temp dir. sqlx's migrator
//! runs the same embedded migrations the server uses, so these tests fail if
//! the schema and the queries ever drift apart.

use {{ package_name }}::store::{normalise_title, Store};

fn temp_db(tag: &str) -> String {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("rsqlx-{tag}-{nanos}"));
    std::fs::create_dir_all(&dir).unwrap();
    dir.join("notes.db").to_string_lossy().to_string()
}

#[tokio::test]
async fn migrations_are_idempotent_and_count_starts_at_zero() {
    let path = temp_db("migrate");
    let first = Store::open(&path).await.unwrap();
    assert_eq!(first.count().await.unwrap(), 0);
    let second = Store::open(&path).await.unwrap();
    assert_eq!(second.count().await.unwrap(), 0);
}

#[tokio::test]
async fn create_list_get_patch_delete_round_trip() {
    let path = temp_db("crud");
    let store = Store::open(&path).await.unwrap();
    let note = store.create("shopping", "milk").await.unwrap();
    assert_eq!(note.id, 1);
    assert_eq!(note.title, "shopping");
    assert_eq!(note.body, "milk");
    assert!(note.created_at.ends_with('Z'));

    let listed = store.list().await.unwrap();
    assert_eq!(listed.len(), 1);
    assert_eq!(listed[0], note);

    let patched = store.patch(note.id, Some("groceries"), None).await.unwrap();
    assert_eq!(patched.title, "groceries");
    assert_eq!(patched.body, "milk", "untouched field must survive a patch");
    assert_eq!(
        patched.created_at, note.created_at,
        "created_at never moves"
    );

    store.delete(note.id).await.unwrap();
    assert_eq!(store.count().await.unwrap(), 0);
    assert!(store.get(note.id).await.is_err());
    assert!(
        store.delete(note.id).await.is_err(),
        "second delete is a 404"
    );
}

#[tokio::test]
async fn rows_survive_a_new_connection() {
    let path = temp_db("persist");
    {
        let store = Store::open(&path).await.unwrap();
        store.create("keep", "me").await.unwrap();
    }
    let reopened = Store::open(&path).await.unwrap();
    assert_eq!(reopened.count().await.unwrap(), 1);
    assert_eq!(reopened.list().await.unwrap()[0].title, "keep");
}

#[test]
fn blank_titles_are_rejected_before_sql() {
    assert!(normalise_title("   ").is_none());
    assert_eq!(normalise_title(" x "), Some("x".to_string()));
}
