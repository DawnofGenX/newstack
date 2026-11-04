# Project title

A SQL reporting project: the schema, the views and the queries are plain `.sql`
files, and the only program is a shell wrapper that runs one report against a
throwaway database.

## Layout

    schema.sql        tables, keys and the CHECK constraints that guard them
    views.sql         order_totals and customer_revenue: the arithmetic, once
    seed.sql          deterministic sample data the tests can assert exactly
    queries/          one SELECT per report, in top_customers.sql and friends
    bin/NAME          builds a scratch database and prints one report
    tests/run_tests.sh  the numbers, the constraints and the cascade
    Makefile          db / test / report / clean

## Running it

    make db                  # build/app.db
    make test                # the assertions
    ./bin/NAME --list
    ./bin/NAME top_customers

## What it prints

    $ ./bin/NAME top_customers
    Bruno|2|87.00
    Chen|1|82.50
    Asha|2|43.50
    Dana|0|0.00

Every report goes through a view, so a revenue change is one edit in
`views.sql` and every query follows. `PRAGMA foreign_keys = ON` is repeated in
each file because SQLite defaults it off per connection, and `ON DELETE
CASCADE` is what makes deleting a customer remove their orders and lines.

The seed is deterministic: the same rows on every build, which is why the tests
can assert exact cents rather than a range.
