.PHONY: migrate seed test build up down sync-vectors

migrate:
	cd backend && POSTGRES_HOST=localhost poetry run alembic upgrade head

seed:
	cd backend && POSTGRES_HOST=localhost poetry run python3 seed.py

test:
	cd backend && PYTHONPATH=. POSTGRES_HOST=localhost poetry run pytest

build:
	docker-compose build

up:
	docker-compose up -d --build

down:
	docker-compose down

sync-vectors:
	cd rag_engine && POSTGRES_HOST=localhost QDRANT_HOST=localhost poetry run python scripts/sync_vectors.py
