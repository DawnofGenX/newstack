package cmd

import (
	"fmt"
	"os"

	"{{ npm_name }}/internal/app"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:     "{{ npm_name }}",
	Short:   "{{ description }}",
	Version: "0.1.0",
}

var greetCmd = &cobra.Command{
	Use:   "greet [name]",
	Short: "greet someone",
	Args:  cobra.MaximumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		name := ""
		if len(args) > 0 {
			name = args[0]
		}
		fmt.Println(app.Greet(name))
	},
}

var addCmd = &cobra.Command{
	Use:   "add <a> <b>",
	Short: "add two numbers",
	Args:  cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		var a, b int
		if _, err := fmt.Sscan(args[0], &a); err != nil {
			return err
		}
		if _, err := fmt.Sscan(args[1], &b); err != nil {
			return err
		}
		fmt.Println(app.Add(a, b))
		return nil
	},
}

func init() {
	rootCmd.AddCommand(greetCmd, addCmd)
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}