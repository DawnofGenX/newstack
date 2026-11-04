APP ?= {{ npm_name }}
DB  ?= build/app.db

.PHONY: all db test report clean

all: db

db: $(DB)

$(DB): schema.sql views.sql seed.sql
	@mkdir -p build
	@rm -f $(DB)
	@sqlite3 $(DB) < schema.sql
	@sqlite3 $(DB) < views.sql
	@sqlite3 $(DB) < seed.sql
	@echo "built $(DB)"

test: db
	@sh tests/run_tests.sh

report: db
	@sqlite3 -batch -separator '|' $(DB) "SELECT 'top_customers';" ".read queries/top_customers.sql" \
	  "SELECT 'monthly';" ".read queries/monthly.sql" \
	  "SELECT 'countries';" ".read queries/countries.sql"

clean:
	@rm -rf build
