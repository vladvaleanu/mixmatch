# Pasul 10b — Exportul: tracklist, .cue, ecranul

## Ce am găsit înainte
`export/render.py` (randarea, `_timelines` cu începutul fiecărei tranziții), `api/exports.py`
(`POST /mixes/{id}/export`, numele fișierelor), fereastra de export din Constructor, ecranul Exporturi gol.
Decizii de dinainte: tabelul `exports`, `GET /exports`, `GET /exports/{id}/file`.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/export/render.py` | schimbat | `RenderResult` (durata + începutul fiecărei piese) | `api/exports.py` |
| `backend/mixmatch/export/tracklist.py` | nou | tracklistul text și .cue | jobul de export |
| `backend/mixmatch/db/models.py` + migrarea `0007` | schimbat/nou | tabelul `exports` | API |
| `backend/mixmatch/api/exports.py`, `api/jobs.py` | schimbat | rândul `exports`, scrierea .txt/.cue, lista, descărcarea; `job_out` public | ecranul |
| `backend/tests/test_tracklist.py`, `test_api_exports.py`, `test_export.py`, `conftest.py` | nou/schimbat | formate, listă, descărcări, mix șters | `make test` |
| `frontend/src/api/exports.ts` | schimbat | `useExports` (cu reîmprospătare), `exportFileUrl` | ecranul |
| `frontend/src/features/exports/ExportsScreen.tsx` (+ test), `ExportDialog.tsx`, `i18n/ro.ts` | nou/schimbat | lista, progresul, descărcările; „Vezi în Exporturi” | — |

## Ce s-a făcut
- Fiecare export scrie lângă audio tracklistul (`.txt`) și `.cue`, cu momentul fiecărei piese.
- Ecranul Exporturi: cele mai noi primele; numele mixului, formatul, data, durata, calea; progresul în timp
  real; „Descarcă audio”, „Tracklist”, „.cue”; „Deschide mixul”; mesaje pentru exporturi eșuate, fișiere
  lipsă și mixuri șterse.

## Verificat („timpii din tracklist corespund cu fișierul randat”)
- Mixul de test exportat ca WAV (57,8 min) cu tracklist și .cue.
- Pentru fiecare tranziție am măsurat în audio, secundă cu secundă, cât din A și cât din B e în export:
  momentul din tracklist cade de fiecare dată în tranziție, la 0–15 s de punctul în care B devine mai tare
  decât A (3 din 8 exact). Timpii vin din aceeași cronologie ca randarea.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (începutul unei piese, formatele, tabelul și API-ul, reîmprospătarea).

## Cum testezi
- `make lint && make test && make types` (396 de teste backend, 60 frontend).
- `make dev` → un mix → „Exportă” → „Vezi în Exporturi” → descarcă audio, tracklist, .cue.

## Ce rămâne / atenție pentru pasul următor
- Pasul 11: finisaje (drag & drop cu upload, colecții și tag-uri, stări goale, scurtături).
- Pasul 8c așteaptă încă ascultarea.
- Artiștii din tracklist vin din tag-uri: unele fișiere au artiști repetați („…, Alex Mills, Alex Mills, …”).
- În `~/Music/mixmatch/Test beatmatch — ascultă tranzițiile/` sunt acum un MP3 (139 MB) și un WAV (~600 MB) de test.
