package main

import (
	"embed"
	"fmt"
	"io/fs"
	"os"

	"{{ npm_name }}/internal/migrate"
)

//go:embed migrations/*.sql
var migrationsFS embed.FS

func migrations() fs.FS { return migrationsFS }

func main() {
	if len(os.Args) < 2 {
		fmt.Println("usage: migrate <up|status> [db-path]")
		os.Exit(2)
	}
	cmd := os.Args[1]
	dbPath := "app.db"
	if len(os.Args) >= 3 {
		dbPath = os.Args[2]
	}
	db, err := migrate.Open(dbPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer db.Close()

	switch cmd {
	case "up":
		if err := migrate.Up(db, migrations()); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println("migrations applied")
	case "status":
		lines, err := migrate.StatusLines(db, migrations())
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		for _, l := range lines {
			fmt.Println(l)
		}
	default:
		fmt.Println("usage: migrate <up|status> [db-path]")
		os.Exit(2)
	}
}