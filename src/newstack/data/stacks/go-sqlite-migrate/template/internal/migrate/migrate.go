package migrate

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"io/fs"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	_ "modernc.org/sqlite"
)

type Migration struct {
	Version  int
	Name     string
	Path     string
	SQL      string
	Checksum string
}

func LoadMigrations(fsys fs.FS) ([]Migration, error) {
	entries, err := fs.ReadDir(fsys, "migrations")
	if err != nil {
		// support fs rooted at migrations
		entries, err = fs.ReadDir(fsys, ".")
		if err != nil {
			return nil, err
		}
	}
	var out []Migration
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if !strings.HasSuffix(name, ".sql") {
			continue
		}
		data, err := fs.ReadFile(fsys, filepath.Join("migrations", name))
		if err != nil {
			data, err = fs.ReadFile(fsys, name)
			if err != nil {
				return nil, err
			}
		}
		version := 0
		for i, c := range name {
			if c < '0' || c > '9' {
				if i == 0 {
					return nil, fmt.Errorf("migration %s lacks numeric prefix", name)
				}
				version, _ = strconv.Atoi(name[:i])
				break
			}
		}
		sum := sha256.Sum256(data)
		out = append(out, Migration{
			Version:  version,
			Name:     strings.TrimSuffix(name, ".sql"),
			Path:     name,
			SQL:      string(data),
			Checksum: hex.EncodeToString(sum[:]),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Version < out[j].Version })
	return out, nil
}

func Open(path string) (*sql.DB, error) {
	return sql.Open("sqlite", path)
}

func EnsureTable(db *sql.DB) error {
	_, err := db.Exec(`CREATE TABLE IF NOT EXISTS schema_migrations (
		version INTEGER PRIMARY KEY,
		name TEXT NOT NULL,
		checksum TEXT NOT NULL,
		applied_at TEXT NOT NULL DEFAULT (datetime('now'))
	)`)
	return err
}

func AppliedVersions(db *sql.DB) (map[int]string, error) {
	if err := EnsureTable(db); err != nil {
		return nil, err
	}
	rows, err := db.Query("SELECT version, checksum FROM schema_migrations")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[int]string{}
	for rows.Next() {
		var v int
		var c string
		if err := rows.Scan(&v, &c); err != nil {
			return nil, err
		}
		out[v] = c
	}
	return out, rows.Err()
}

func VerifyApplied(db *sql.DB, migrations []Migration) error {
	applied, err := AppliedVersions(db)
	if err != nil {
		return err
	}
	byVersion := map[int]Migration{}
	for _, m := range migrations {
		byVersion[m.Version] = m
	}
	for v, c := range applied {
		m, ok := byVersion[v]
		if !ok {
			return fmt.Errorf("applied migration %d not found in embedded set", v)
		}
		if m.Checksum != c {
			return fmt.Errorf("checksum mismatch for migration %d (%s): db=%s file=%s", v, m.Name, c, m.Checksum)
		}
	}
	return nil
}

func Up(db *sql.DB, fsys fs.FS) error {
	migrations, err := LoadMigrations(fsys)
	if err != nil {
		return err
	}
	if err := EnsureTable(db); err != nil {
		return err
	}
	if err := VerifyApplied(db, migrations); err != nil {
		return err
	}
	applied, err := AppliedVersions(db)
	if err != nil {
		return err
	}
	for _, m := range migrations {
		if _, ok := applied[m.Version]; ok {
			continue
		}
		tx, err := db.Begin()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(m.SQL); err != nil {
			_ = tx.Rollback()
			return fmt.Errorf("migration %d (%s): %w", m.Version, m.Name, err)
		}
		if _, err := tx.Exec("INSERT INTO schema_migrations(version,name,checksum) VALUES (?,?,?)", m.Version, m.Name, m.Checksum); err != nil {
			_ = tx.Rollback()
			return err
		}
		if err := tx.Commit(); err != nil {
			return err
		}
	}
	return nil
}

func StatusLines(db *sql.DB, fsys fs.FS) ([]string, error) {
	migrations, err := LoadMigrations(fsys)
	if err != nil {
		return nil, err
	}
	applied, err := AppliedVersions(db)
	if err != nil {
		return nil, err
	}
	var lines []string
	for _, m := range migrations {
		state := "pending"
		if _, ok := applied[m.Version]; ok {
			state = "applied"
		}
		lines = append(lines, fmt.Sprintf("%03d  %-28s %s", m.Version, m.Name, state))
	}
	return lines, nil
}