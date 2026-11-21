# Pasul 12 — Rularea pe server (Docker)

În afara planului inițial (pașii 0–11): cerut de utilizator după mutarea de pe Mac. Aplicația nu mai
rulează pe calculatorul de lucru, ci pe serverul de acasă `homebox`.

## Ce am găsit înainte
- Serverul: AlmaLinux 10.2, AMD Opteron X3216 (2 nuclee, AVX2), 30 GB RAM, Docker 29.6 + compose v5.3,
  SELinux activ (folderele `/opt/docker/appdata` și `/srv/media/music` au deja eticheta `container_file_t`),
  utilizatorul `valeu` = 1000:1000, IP rezervat 192.168.2.140. Portul 8090 e accesibil din rețea (verificat
  cu un container temporar, șters apoi).
- Aplicația pornea doar cu `make dev`: Vite servea interfața și trimitea `/api` la uvicorn; nu exista un mod
  de producție. Frontendul folosește `BrowserRouter` și `window.location.origin` (nicio adresă fixă) și nicio
  funcție care cere HTTPS.
- `essentia` și `numpy` nu erau în `pyproject.toml` (instalate de mână pe Mac) → `make setup` era incomplet.
- Datele Docker ale serverului sunt în `/srv/docker` (RAID), nu pe SSD — setarea serverului, nu a proiectului.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `Dockerfile`, `.dockerignore` | noi | imaginea: frontend compilat (cu lint + teste), Python 3.12 + ffmpeg, etapa `test` | `compose.yaml`, `docker build --target test` |
| `compose.yaml` | nou | portul 8090, montările SSD/RAID, utilizatorul 1000:1000, repornire automată | serverul |
| `backend/mixmatch/main.py`, `config.py` | schimbat | `mount_frontend`: servește `frontend/dist` (cu `index.html` pentru rutele din browser) | imaginea |
| `backend/tests/test_frontend.py` | nou | interfața, rutele din browser, `/api` necunoscut = 404 JSON, fără fișiere din afara `dist` | `pytest` |
| `backend/mixmatch/analysis/runner.py` | schimbat | procesele de analiză cu `spawn` | analiza |
| `backend/pyproject.toml` | schimbat | `essentia`, `numpy` | instalarea |
| `README.md`, `docs/decisions.md` | schimbat | cum se folosește serverul; deciziile | — |

## Ce s-a făcut
- Imaginea în patru etape: `frontend` (`npm ci`, `npm run lint`, `npm test`, `npm run build`), `base`
  (Python 3.12 slim + ffmpeg Debian, dependențele într-un strat separat), `test` (ruff + pytest), finală.
- Backendul servește interfața din `MIXMATCH_FRONTEND_DIR` dacă există `index.html`; în dezvoltare nu există
  `dist`, deci `make dev` rămâne neschimbat. Ruta nu apare în OpenAPI (schema are tot 24 de rute `/api`).
- **Găsit pe Linux:** testele au arătat avertismentul Python 3.12 „process is multi-threaded, use of fork()
  may lead to deadlocks”. Analiza pornea procese cu `fork` (implicit pe Linux) din serverul cu fire. Acum
  pornesc explicit cu `spawn`, ca pe macOS, unde fusese testat totul.

## Decizii
- Primele intrări din `docs/decisions.md` (serverul, imaginea, servirea interfeței, căile, `spawn`, dependențele).

## Cum testezi
- Pe server: `docker build --target test .` (ruff + 409 teste backend) și `docker compose up -d --build`
  (lint + 67 teste frontend + build).
- Din rețea: http://192.168.2.140:8090 → Biblioteca; `GET /api/health` → `{"status": "ok"}`.

## Ce rămâne / atenție
- Muzica nu e încă pe server (`/srv/media/music` e gol); după copiere, folderele se adaugă ca `/music/...`.
- Analiza rulează cu un singur proces (2 nuclee) — biblioteca mare durează.
- Rămân deschise: confirmarea prin ascultare a pasului 8c și ideea „Ascultă mixul”.
- Terminațiile de linie: pe Windows (`core.autocrlf=true`) fișierele din folder au CRLF; imaginea se construiește
  din clona de pe server (LF), deci nu contează acolo.
