# Everything the project does, behind one command each.
PORT ?= 8080
export PORT

.PHONY: help build up down smoke test logs

help: ## show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

build: ## build the image
	docker compose build

up: ## start the service and wait until it is healthy
	docker compose up -d --build --wait

down: ## stop it and remove the container
	docker compose down --remove-orphans

smoke: ## run the HTTP smoke test against a real container
	./tests/smoke.sh

test: ## unit tests, no Docker needed
	python3 -m unittest discover -s tests -p 'test_*.py' -v

logs: ## follow the container's log
	docker compose logs -f --tail 50
