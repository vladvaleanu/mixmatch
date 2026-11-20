# Pasul 01 — Baza de date

## Ce am găsit înainte
Backend FastAPI cu `config.py` (doar versiunea), `main.py` (montează `api/health.py` sub `/api`).
Convenții: rutele sub `/api`, `operation_id` explicit, ruff cu linia de 100, teste cu
`TestClient`. Pasul se leagă prin `config.py` (calea bazei) și `main.py` (pornirea).
Decizii noi luate înainte de pas: tranzițiile legate de pereche, tabelul `exports` (pasul 10b).

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/pyproject.toml` | schimbat | sqlalchemy, alembic | tot backendul |
| `backend/mixmatch/config.py` | schimbat | `data_dir`, `db_url`, căile repo-ului | `db/session.py`, `alembic/env.py` |
| `backend/mixmatch/db/models.py` | nou | `Track`, `LibraryFolder`, `Job` (+ `JobKind`, `JobStatus`) | `jobs.py`, migrările, pasul 2 |
| `backend/mixmatch/db/session.py` | nou | engine SQLite (WAL, FK), `SessionLocal`, `run_migrations` | `jobs.py`, `main.py`, teste |
| `backend/alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` | noi | configurarea Alembic | `run_migrations`, CLI-ul alembic |
| `backend/alembic/versions/0001_…py` | nou | prima migrare: cele trei tabele | `run_migrations` |
| `backend/mixmatch/jobs.py` | nou | `JobQueue` (thread pool + starea în `jobs`), `queue` global | `main.py`; pasul 2 (scanare) |
| `backend/mixmatch/main.py` | schimbat | lifespan: migrări, joburi întrerupte, oprirea cozii | uvicorn |
| `backend/tests/conftest.py` | nou | bază temporară migrată pentru fiecare test | testele |
| `backend/tests/test_migrations.py`, `test_models.py`, `test_jobs.py` | noi | testele pasului | `make test` |

## Ce s-a făcut
- Tabelele `tracks` (toate coloanele din plan), `library_folders`, `jobs`, cu `path` unic,
  index pe `file_hash` și constrângeri pentru energie (1–5) și progres (0–1).
- `JobQueue.submit(kind, fn)` creează rândul în `jobs` și rulează `fn(report)` într-un fir;
  starea trece prin `queued → running → done/failed`, eroarea se păstrează în `error`.
- La pornire: migrări până la `head`, apoi joburile neterminate devin `failed` („întrerupt”).

## Decizii
- Vezi primele intrări din `docs/decisions.md` (locația bazei, WAL, migrări la pornire,
  stările joburilor, naming convention, testul modele vs. migrări).

## Cum testezi
- `make lint && make test && make types` (16 teste backend, 2 frontend).
- `make dev` → apare `data/mixmatch.db`; `sqlite3 data/mixmatch.db .tables` arată
  `alembic_version jobs library_folders tracks`.
- Migrare nouă după ce schimbi modelele:
  `cd backend && .venv/bin/alembic revision --autogenerate --rev-id 0002 -m "<ce>"`.

## Ce rămâne / atenție pentru pasul următor
- Nicio rută nu folosește încă baza; pasul 2 adaugă o dependență de sesiune pentru FastAPI,
  `POST /library/folders`, `GET /jobs/{id}`, `GET /tracks` și forma de eroare `{"error": …}`.
- `tracks` nu are încă o legătură cu `library_folders`; dacă rescanarea are nevoie de ea, pasul 2
  o adaugă printr-o migrare.
- Pasul 2: formatele MP3, FLAC, WAV, AIFF, M4A; fișierele sub 60 s se ignoră (prag în `config.py`).
- Valoarea efectivă a energiei (`energy_manual ?? energy`) nu există încă în cod; apare în 3b.
