# {{ title }}

A small Rails 8 application whose one job is to count lines, words and bytes. The
counting lives in `app/services/text_stat.rb` — a plain class that takes a string and
returns three numbers — so the interesting logic can be tested without booting a
server.

## Requirements

Ruby 3.2 or newer and Bundler. Rails 8.1 itself is installed by `bundle install`; it
is not a system gem.

## Setup

    bin/setup --skip-server

`bin/setup` installs the gems into `vendor/bundle` (`.bundle/config` sets
`BUNDLE_PATH`, so nothing is written into the system gem directory), prepares the
SQLite database under `storage/` and clears the logs.

## Run it

    bin/rails server

    curl 'http://127.0.0.1:3000/stats?text=alpha+beta%0Agamma%0A'
    {"lines":2,"words":3,"bytes":17}

`GET /stats` without `text` answers 400 with `{"error":"missing the text parameter"}`,
and `GET /up` is Rails' health check: 200 while the app boots.

## Test it

    bin/rails test
    8 runs, 10 assertions, 0 failures, 0 errors, 0 skips

`test/services/text_stat_test.rb` exercises the counter directly;
`test/controllers/stats_controller_test.rb` is an integration test that goes through
the router, so a broken route or a renamed parameter fails the suite.

## Where things are

    app/services/text_stat.rb                        the counter (no Rails code)
    app/controllers/stats_controller.rb              GET /stats, JSON in and out
    app/views/layouts/application.html.erb           the layout for HTML views
    config/routes.rb                                 /up and /stats
    config/database.yml                              SQLite in storage/
    test/                                            the two test files above
    .github/workflows/ci.yml                         tests, wc parity and a live request

## Deployment notes

`config/master.key` and `config/credentials.yml.enc` are deliberately absent: this
starter keeps no encrypted secrets. Generate them with `bin/rails credentials:edit`
when you need them, and set `RAILS_MASTER_KEY` wherever you deploy. Remember to run
`bin/rails db:prepare` against the production database.
