API_DIR := apps/api
WEB_DIR := apps/web
PYTHON := $(API_DIR)/.venv/bin/python
ALEMBIC := $(API_DIR)/.venv/bin/alembic

.PHONY: dev migrate test test-unit test-integration lint build seed index sync-news extract-triggers semantic-install semantic-download semantic-offline-smoke semantic-host-check

dev:
	docker compose up --build

migrate:
	cd $(API_DIR) && .venv/bin/python -m scripts.migrate

test: test-unit test-integration

test-unit:
	cd $(API_DIR) && .venv/bin/python -m pytest tests/unit -q

test-integration:
	cd $(API_DIR) && .venv/bin/python -m pytest tests/integration -q

lint:
	cd $(API_DIR) && .venv/bin/python -m compileall -q app main.py alembic tests
	cd $(WEB_DIR) && pnpm lint

build:
	cd $(API_DIR) && .venv/bin/python -m compileall -q app main.py alembic
	cd $(WEB_DIR) && pnpm build

seed:
	cd $(API_DIR) && .venv/bin/python scripts/seed_data.py

index:
	cd $(API_DIR) && .venv/bin/python scripts/index_documents.py

sync-news:
	@test -n "$(M3_TEST_DATABASE_URL)" || (echo "M3_TEST_DATABASE_URL is required" && exit 1)
	cd $(API_DIR) && .venv/bin/python -m scripts.sync_news --database-url "$(M3_TEST_DATABASE_URL)"

extract-triggers:
	@test -n "$(M3_TEST_DATABASE_URL)" || (echo "M3_TEST_DATABASE_URL is required" && exit 1)
	cd $(API_DIR) && .venv/bin/python -m scripts.extract_triggers --database-url "$(M3_TEST_DATABASE_URL)"

semantic-install:
	cd $(API_DIR) && .venv/bin/python -m pip install -r requirements-semantic.txt

semantic-download:
	@test -n "$(HF_MODEL_CACHE_DIR)" || (echo "HF_MODEL_CACHE_DIR is required" && exit 1)
	cd $(API_DIR) && .venv/bin/python -m scripts.download_embedding_model --cache-dir "$(HF_MODEL_CACHE_DIR)"

semantic-offline-smoke:
	@test -n "$(HF_MODEL_CACHE_DIR)" || (echo "HF_MODEL_CACHE_DIR is required" && exit 1)
	cd $(API_DIR) && HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 EMBEDDING_PROVIDER=sentence_transformer HF_MODEL_CACHE_DIR="$(HF_MODEL_CACHE_DIR)" .venv/bin/python -c "from app.services.embedding_service import EmbeddingService; v=EmbeddingService().embed_text('offline semantic smoke'); assert len(v)==384; assert all(x==x and abs(x)!=float('inf') for x in v); print('offline MiniLM smoke passed: 384 finite values')"

semantic-host-check:
	@test -n "$(HF_MODEL_CACHE_DIR)" || (echo "HF_MODEL_CACHE_DIR is required" && exit 1)
	cd $(API_DIR) && EMBEDDING_PROVIDER=sentence_transformer HF_MODEL_CACHE_DIR="$(HF_MODEL_CACHE_DIR)" .venv/bin/python -m scripts.semantic_probe
