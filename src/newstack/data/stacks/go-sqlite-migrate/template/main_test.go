package main

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"

	"{{ npm_name }}/internal/migrate"
)

func TestUpIdempotent(t *testing.T) {
	dir := t.TempDir()
	dbPath := filepath.Join(dir, "test.db")
	db, err := migrate.Open(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err := migrate.Up(db, migrations()); err != nil {
		t.Fatal(err)
	}
	// table exists
	var n int
	if err := db.QueryRow("SELECT COUNT(*) FROM items").Scan(&n); err != nil {
		t.Fatal(err)
	}
	// idempotent
	if err := migrate.Up(db, migrations()); err != nil {
		t.Fatal(err)
	}
}

func TestStatus(t *testing.T) {
	dir := t.TempDir()
	dbPath := filepath.Join(dir, "test.db")
	db, _ := migrate.Open(dbPath)
	defer db.Close()
	_ = migrate.Up(db, migrations())
	lines, err := migrate.StatusLines(db, migrations())
	if err != nil {
		t.Fatal(err)
	}
	if len(lines) != 2 {
		t.Fatalf("lines=%d", len(lines))
	}
}

func TestChecksumMismatch(t *testing.T) {
	dir := t.TempDir()
	dbPath := filepath.Join(dir, "test.db")
	db, _ := migrate.Open(dbPath)
	defer db.Close()
	if err := migrate.Up(db, migrations()); err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec("UPDATE schema_migrations SET checksum='bad' WHERE version=1"); err != nil {
		t.Fatal(err)
	}
	if err := migrate.Up(db, migrations()); err == nil {
		t.Fatal("expected checksum mismatch error")
	}
	_ = sql.Open
	_ = os.Args
}