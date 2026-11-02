// Command {{ npm_name }} is {{ description }}
package main

import (
	"os"

	"{{ npm_name }}/internal/app"
)

func main() {
	os.Exit(app.Run(os.Args[1:], os.Stdout, os.Stderr))
}
