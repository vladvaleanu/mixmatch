# Pasul 00 — Scheletul

## Ce am găsit înainte
Doar documentația (plan, decizii, design, machete). Nu exista cod. Pe mașină: `python3` e 3.11,
dar există `/opt/homebrew/bin/python3.12`; Node 22; ffmpeg 7.0.1 (fără filtrul rubberband).
Bara de sus din machete: logo (cerc cu punct), nav pastile, căutare, buton principal.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `Makefile` | nou | setup, check-tools, dev, test, lint, format, types | utilizatorul, fiecare pas |
| `.gitignore` | schimbat | ignoră `backend/openapi.json` (generat) | git |
| `backend/pyproject.toml` | nou | pachetul `mixmatch`, dependențe, ruff, pytest | `make setup/lint/test` |
| `backend/mixmatch/config.py` | nou | setările (deocamdată versiunea) | `main.py`, `api/health.py` |
| `backend/mixmatch/main.py` | nou | aplicația FastAPI, montează rutele sub `/api` | uvicorn, teste, `openapi.py` |
| `backend/mixmatch/api/health.py` | nou | `GET /api/health` | frontend (`api/health.ts`) |
| `backend/mixmatch/openapi.py` | nou | scrie schema OpenAPI fără server | `make types` |
| `backend/tests/test_health.py` | nou | testul rutei | `make test` |
| `frontend/package.json`, `tsconfig*.json`, `vite.config.ts`, `eslint.config.js`, `.prettierrc.json`, `.prettierignore`, `index.html` | noi | Vite + React 18 + TS strict, proxy `/api` → 8000, Vitest, lint | `make dev/test/lint` |
| `frontend/src/api/schema.d.ts` | nou (generat) | tipurile din OpenAPI | `api/client.ts` |
| `frontend/src/api/client.ts` | nou | singurul loc cu `fetch`, tipat din schema | `api/health.ts` |
| `frontend/src/api/health.ts` | nou | hook-ul `useHealth` (TanStack Query) | `ui/TopBar.tsx` |
| `frontend/src/theme/tokens.ts` | nou | culori, fonturi, spațieri, raze din design.md | toate componentele |
| `frontend/src/theme/GlobalStyle.tsx` | nou | stilurile de bază generate din tokens | `main.tsx` |
| `frontend/src/i18n/ro.ts` | nou | textele interfeței | toate componentele |
| `frontend/src/ui/TopBar.tsx` (+ test) | nou | logo, navigarea, starea serverului | `App.tsx` |
| `frontend/src/ui/ScreenHeader.tsx` | nou | H1 + subtitlu, comun celor trei ecrane | ecranele din `features/` |
| `frontend/src/features/{library,mix-builder,exports}/*Screen.tsx` | noi | ecranele goale | `App.tsx` |
| `frontend/src/App.tsx`, `main.tsx` | noi | shell-ul, rutele, providerii | `index.html` |

## Ce s-a făcut
- Backend FastAPI cu `GET /api/health` → `{"status": "ok", "version": "0.1.0"}`.
- Frontend Vite 8 + React 18 + TS strict. `TopBar` ca în machetă (logo, nav pastile cu
  pastila activă pe `surface3`) și un indicator de stare a serverului în dreapta
  (punct accent = conectat, warn = nu răspunde; verificare la 10 s).
- Rute: `/biblioteca`, `/mixuri`, `/exporturi`; `/` și orice altă rută duc la `/biblioteca`.
- `make types` generează `schema.d.ts`; `api/client.ts` deduce tipul răspunsului din cale.
- Fonturile Inter și Space Grotesk se încarcă local (@fontsource).

## Decizii
- Vezi intrările din 2026-11-20 de la începutul `docs/decisions.md` (python3.12, dependențe,
  rutare, fonturi locale, stiluri inline din tokens, `accentSoftBgStrong`, fluxul `make types`).

## Cum testezi
- `make setup` (o dată), apoi `make lint && make test && make types`.
- `make dev` → http://localhost:5173: bara de sus, „Server conectat”. Oprește backendul →
  după ≤10 s apare „Serverul nu răspunde”.
- Notă: Vite ascultă pe `localhost` (IPv6 `::1`); `curl 127.0.0.1:5173` nu răspunde, `localhost:5173` da.

## Ce rămâne / atenție pentru pasul următor
- Căutarea și butonul principal din `TopBar` („Importă piese”) nu sunt încă puse: nu fac nimic
  până la pasul 2. Butonul principal diferă pe ecrane (Biblioteca: „Importă piese”, Constructor: „Exportă”).
- Forma de eroare `{"error": {...}}` și toast-ul global nu există încă; apar odată cu prima
  rută care poate eșua (pasul 2).
- `config.py` are doar versiunea; pasul 1 adaugă calea bazei de date.
- ffmpeg-ul instalat nu are rubberband (relevant la pasul 10a).
