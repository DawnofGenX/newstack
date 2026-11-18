# ruby-luhn-cli

A small Ruby CLI that validates Luhn checksums (credit-card numbers), generates a
check digit for a prefix, and identifies the card brand. Stdlib only: no bundler,
minitest + rake.

## Usage

    rake test
    bin/ruby-luhn-cli validate 4111111111111111
    bin/ruby-luhn-cli generate 411111111111111
    bin/ruby-luhn-cli brand 4111111111111111
