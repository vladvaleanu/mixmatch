# Pasul 02 — Scanarea bibliotecii

## Ce am găsit înainte
Backend: `db/models.py` (Track, LibraryFolder, Job), `jobs.py` (`JobQueue.submit(kind, fn)` cu
`report(progress)`), sesiuni în `db/session.py`, rute sub `/api` cu `operation_id` explicit.
Frontend: `api/client.ts` scris de mână peste `schema.d.ts`, `ui/` cu TopBar și ScreenHeader,
ecrane goale în `features/`. Nu existau forma de eroare, toast-ul și componentele de formular.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/pyproject.toml` | schimbat | mutagen; `pythonpath` pentru `tests/` | tot |
| `backend/mixmatch/config.py` | schimbat | `audio_extensions`, `min_duration_s = 60` | `library/scan.py` |
| `backend/mixmatch/library/scan.py` | nou | găsește fișierele, citește metadatele (inclusiv RIFF INFO), `file_hash`, upsert/ștergere | `api/library.py` |
| `backend/mixmatch/jobs.py` | schimbat | pool-ul se recreează după shutdown | lifespan, teste |
| `backend/mixmatch/api/errors.py` | nou | `ApiError`, forma `{"error": …}`, handler-e | toate rutele |
| `backend/mixmatch/api/deps.py` | nou | `SessionDep` | rutele |
| `backend/mixmatch/api/library.py` | nou | `POST /library/folders` | `frontend/api/library.ts` |
| `backend/mixmatch/api/jobs.py` | nou | `GET /jobs/{id}` | `frontend/api/jobs.ts` |
| `backend/mixmatch/api/tracks.py` | nou | `GET /tracks` (id, titlu, artist, durată) | `frontend/api/tracks.ts` |
| `backend/mixmatch/main.py` | schimbat | montează rutele și handler-ele de erori | uvicorn |
| `backend/tests/audio.py`, `test_scan.py`, `test_api_library.py` | noi | fișiere audio generate cu ffmpeg; testele pasului | `make test` |
| `frontend/src/api/client.ts` | schimbat | openapi-fetch + `unwrap` → `ApiError` | toate hook-urile |
| `frontend/src/api/{tracks,library,jobs}.ts` | noi | `useTracks`, `useAddFolder`, `useJob` (polling 500 ms) | ecranul Biblioteca |
| `frontend/src/api/queryClient.ts` | nou | erorile Query → toast (fără `meta.silent`) | `main.tsx`, teste |
| `frontend/src/ui/{Button,Dialog,ProgressBar,PlusIcon,Toast}.tsx`, `toastStore.ts`, `format.ts` | noi | componentele dialogului și ale tabelului | Biblioteca, App |
| `frontend/src/ui/TopBar.tsx` | schimbat | slot `actions` pentru butonul principal | `App.tsx` |
| `frontend/src/features/library/*` | noi/schimbat | ecranul, tabelul, dialogul, butonul „Importă piese”, starea dialogului | `App.tsx` |
| `frontend/src/theme/tokens.ts`, `i18n/ro.ts` | schimbat | `overlay`, `zIndex`; textele noi | toate |
| `frontend/src/testing.tsx` | nou | `mockApi`, `renderWithProviders` | testele |

## Ce s-a făcut
- Scanarea parcurge folderul recursiv (MP3, FLAC, WAV, AIFF, M4A), sare peste fișierele ascunse,
  stricate și sub 60 s, și salvează la fiecare 50 de fișiere (tabelul se umple în timp ce scanează).
- Rescanarea: aceeași cale → același rând (fără duplicate); fișier schimbat → rând actualizat;
  fișier dispărut → rând șters. Același folder adăugat din nou = rescanare.
- Biblioteca: titlu, subtitlu, numărul de piese, zona punctată „Adaugă un folder…”, tabelul
  (Piesă: titlu + artist; Durată). Dialogul: cale → „Scanează” → bară de progres → „Gata!”.
- Erorile API au forma `{"error": {code, message}}` și apar într-un toast global.

## Verificat pe biblioteca reală
- `~/Music/House 🏠 Set 1`: 38 de MP3, toate adăugate în 0,3 s; rescanarea → tot 38.
- `~/Music/tech house gramada`: 209 M4A → 208 adăugate (1 sărit), sub 2 s.
- Multe piese nu au artist în tag-uri (ex. descărcate de pe YouTube); apar ca „Artist necunoscut”.
- Cele două foldere au rămas în baza ta locală (`data/mixmatch.db`). Dacă vrei să pornești de la
  zero: oprește `make dev` și șterge `data/mixmatch.db`.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (mutagen, zustand, openapi-fetch, hash parțial,
  RIFF INFO, numele fișierului, ștergerea pieselor dispărute, 409 la scanări simultane, toast).

## Cum testezi
- `make lint && make test && make types` (32 de teste backend, 9 frontend).
- `make dev` → „Importă piese” → lipește calea unui folder → „Scanează”.

## Ce rămâne / atenție pentru pasul următor
- Pasul 3a pornește analiza automat după scanare. Piesele noi sau cu `file_hash` schimbat au nevoie
  de analiză; `scan_folder` întoarce deja `ScanResult` (adăugate/actualizate), dar nu și id-urile.
- Coperta din tabel depinde de ton (culoarea Camelot), deci apare în 3a, odată cu coloanele BPM și Ton.
- Căutarea din bara de sus (`q`) și sortarea vin în pasul 5.
- `tracks` nu are o legătură cu `library_folders`; ștergerea pieselor dispărute folosește prefixul căii.
