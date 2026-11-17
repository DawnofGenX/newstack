#!/usr/bin/env node
import { Command } from "commander";

export function greet(name) {
  return `Hello, ${name}!`;
}

export function add(a, b) {
  return Number(a) + Number(b);
}

export function buildProgram() {
  const program = new Command();
  program.name("{{ npm_name }}").description("{{ description }}").version("0.1.0");

  program
    .command("greet <name>")
    .description("greet someone")
    .action((name) => {
      console.log(greet(name));
    });

  program
    .command("add <a> <b>")
    .description("add two numbers")
    .action((a, b) => {
      console.log(add(a, b));
    });

  return program;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  buildProgram().parse();
}