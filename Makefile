.PHONY: benchmark-sync benchmark-check api-sync api-db-up api-db-down api-migrate api-seed api-dev api-check openapi mobile-sync mobile-dev mobile-check secret-scan check

benchmark-sync:
	uv sync --locked --extra dev

benchmark-check:
	uv run pytest
	uv run ruff check benchmark tests
	uv run mypy benchmark
	uv run python -m benchmark validate-corpus
	uv run python -m benchmark run-fixtures
	uv run python -m benchmark report --fixtures
	uv run python -m benchmark pronunciation-calibration

api-sync:
	cd services/api && uv sync --locked --group dev

api-db-up:
	docker compose -f services/api/docker-compose.yml up -d --wait

api-db-down:
	docker compose -f services/api/docker-compose.yml down

api-migrate:
	cd services/api && uv run alembic upgrade head

api-seed:
	cd services/api && uv run python scripts/seed.py

api-dev:
	cd services/api && uv run uvicorn benma_api.app:app --reload --host 0.0.0.0 --port 8000

api-check:
	cd services/api && uv run pytest
	cd services/api && uv run ruff check .
	cd services/api && uv run mypy
	cd services/api && uv run python scripts/export_openapi.py

openapi:
	cd services/api && uv run python scripts/export_openapi.py

mobile-sync:
	npm --prefix apps/mobile ci

mobile-dev:
	npm --prefix apps/mobile start

mobile-check:
	npm --prefix apps/mobile run validate
	cd apps/mobile && CI=1 npx expo export --platform web --output-dir /tmp/benma-expo-web-export
	cd apps/mobile && CI=1 npx expo export --platform android --output-dir /tmp/benma-expo-export

secret-scan:
	bash scripts/scan-secrets.sh

check: benchmark-check api-check mobile-check secret-scan
