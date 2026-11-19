.PHONY: setup dev api lint test test-contract test-integration test-e2e test-roundtrip eval security export-check seed generate-contracts
setup:
	python tools/prepare_local_env.py
	pnpm install
	uv sync --all-packages --all-groups
	docker compose up --detach --wait postgres redis minio mail
	uv run --env-file .env alembic upgrade head
	docker compose run --rm seed

dev:
	docker compose up --detach postgres redis minio mail
	@echo "Web app development server will be added with TSK-033."

api:
	uv run --env-file .env uvicorn prompt_studio_api.main:app --reload

lint:
	pnpm lint:format
	pnpm lint:js
	pnpm lint:types
	uv run ruff check .
	uv run mypy apps backend/app tools

test:
	uv run --env-file .env pytest -q
	pnpm test

test-contract:
	uv run python tools/generate_payload_schemas.py --check
	uv run python tools/generate_artifact_schema.py --check
	pnpm exec node tools/generate_contract_types.mjs --check
	uv run pytest -q tests/contract
	pnpm lint:types

generate-contracts:
	uv run python tools/generate_payload_schemas.py
	uv run python tools/generate_artifact_schema.py
	pnpm exec node tools/generate_contract_types.mjs

test-integration:
	uv run --env-file .env pytest -q tests/integration

test-e2e:
	pnpm exec vitest run packages/canvas/src/excalidraw-adapter.test.ts packages/canvas/src/edge-classification.test.ts

test-roundtrip:
	@echo "Round-trip checks are introduced by TSK-026."

eval:
	@echo "Prompt evaluations are introduced by TSK-044 and TSK-078."

security:
	@echo "Security checks are introduced by TSK-009, TSK-054, and TSK-109."

export-check:
	@echo "Export checks are introduced by TSK-101 and TSK-104."

seed:
	docker compose run --rm seed
