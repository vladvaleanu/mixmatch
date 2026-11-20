# mixmatch — comenzile proiectului. Rulează din rădăcina repo-ului.

PYTHON ?= $(shell command -v python3.12 || command -v python3.13 || command -v python3)
VENV := backend/.venv
PY := $(VENV)/bin/python

.PHONY: setup check-tools dev backend frontend test lint format types

setup: check-tools
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -e "backend[dev]"
	cd frontend && npm install

check-tools:
	@$(PYTHON) -c 'import sys; v=sys.version_info; sys.exit(0 if v >= (3, 12) else f"Python >= 3.12 necesar, găsit {v.major}.{v.minor} ({sys.executable})")'
	@node -e 'const v=+process.versions.node.split(".")[0]; if (v < 20) { console.error("Node >= 20 necesar, găsit " + process.versions.node); process.exit(1) }'
	@command -v ffmpeg >/dev/null || (echo "ffmpeg lipsește (brew install ffmpeg)"; exit 1)
	@echo "Unelte OK: $$($(PYTHON) --version), Node $$(node --version), ffmpeg prezent"

# Pornește backendul (8000) și Vite (5173, cu proxy /api). Ctrl+C le oprește pe amândouă.
dev:
	@trap 'kill 0' INT TERM EXIT; \
	$(MAKE) --no-print-directory backend & \
	$(MAKE) --no-print-directory frontend & \
	wait

backend:
	cd backend && .venv/bin/uvicorn mixmatch.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest -q
	cd frontend && npm test

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd frontend && npm run lint

format:
	cd backend && .venv/bin/ruff check --fix . && .venv/bin/ruff format .
	cd frontend && npm run format

# Schema OpenAPI din backend -> tipurile TypeScript din frontend/src/api/schema.d.ts.
types:
	cd backend && .venv/bin/python -m mixmatch.openapi > openapi.json
	cd frontend && npm run types
