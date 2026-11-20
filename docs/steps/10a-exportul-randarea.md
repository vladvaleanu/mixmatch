# Pasul 10a — Exportul: randarea

## Ce am găsit înainte
`music/transition_plan.py` (planul complet, inclusiv ecoul ca întârzieri și fereastra), `audio/transition.ts`
(execuția în browser), `jobs.py`, `api/transitions.py` cu construcția planului din bază. Decizii de
dinainte: exportul în `~/Music/mixmatch/<mix>/`, WAV 16-bit/44,1 kHz și MP3 320, limiter la export.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/mixes/plans.py` | nou | `side`, `settings_for`, `plan_for` (mutate din API) | editorul, exportul |
| `backend/mixmatch/music/transition_plan.py` | schimbat | `glide_start_s`, `glide_s` (B revine la viteza ei) | exportul |
| `backend/mixmatch/export/render.py` | nou | randarea mixului din planuri | `api/exports.py` |
| `backend/mixmatch/api/exports.py`, `main.py`, `config.py` | nou/schimbat | `POST /mixes/{id}/export`; `exports_dir` (`MIXMATCH_EXPORT_DIR`) | Constructorul |
| `backend/mixmatch/api/transitions.py` | schimbat | folosește `mixes/plans.py`; câmpurile noi | editorul |
| `backend/tests/test_export.py`, `test_api_exports.py`, `conftest.py` | noi/schimbat | piesa singură, revenirea vitezei, low-shelf, erori, API | `make test` |
| `frontend/src/api/exports.ts`, `features/mix-builder/{ExportDialog,MixBuilderScreen}.tsx`, `i18n/ro.ts` | nou/schimbat | „Exportă”: format, progres, calea fișierului | — |
| `frontend/src/audio/plan.ts` | schimbat | începutul bucății lui B nu mai poate fi −0,000 | previzualizarea |

## Ce s-a făcut
- „Exportă” în antetul Constructorului → WAV sau MP3 → bara de progres → „Gata! Fișierul e aici: …”.
- Randarea execută planurile: viteza lui B (stil vinil) cu revenire lină după fereastra de previzualizare,
  volum × auto-gain, low-shelf pentru bas, ecoul; limiter la −1 dB; WAV 16-bit sau MP3 320 kbps.

## Verificat („exportul sună la fel ca previzualizarea, pe trei tranziții”)
- Mixul de test (9 piese, 57,8 min) randat fără limiter în 15,5 s; tranzițiile 1, 4, 7 randate în Chrome cu
  `audio/transition.ts` și comparate cu aceleași momente din export:
  corelație 0,99–1,00 (A singur, mijlocul tranziției, B după), decalaj ≤ 0,02 ms, nivel ±0,1 dB,
  plicul pe toată fereastra: corelație ≥ 0,998, diferență medie ≤ 0,09 dB.
- Prin API, cu limiter: MP3 320 kbps de 57,8 min în 46 s, în
  `~/Music/mixmatch/Test beatmatch — ascultă tranzițiile/`.
- **Găsit și reparat:** la tranziția 1 a mixului de test, începutul bucății lui B ieșea −0,000 (rotunjire),
  serverul îl refuza și „Ascultă tranziția” nu pornea; `clipRanges` nu mai cere începuturi negative.
- Bug mic reparat în timpul testelor: ultimul eșantion al unei piese ieșea 0 la interpolare.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (revenirea vitezei, motorul de randare, limiter-ul doar la
  export, API-ul și numele fișierelor, `mixes/plans.py`).

## Cum testezi
- `make lint && make test && make types` (389 de teste backend, 58 frontend).
- `make dev` → un mix → „Exportă” → MP3 → deschide fișierul din `~/Music/mixmatch/`.

## Ce rămâne / atenție pentru pasul următor
- Pasul 10b: tabelul `exports`, tracklistul cu timpi, fișierul .cue, ecranul Exporturi (lista, progresul,
  descărcarea). Momentele de început ale tranzițiilor (`_timelines`) dau timpii pieselor.
- Dacă o piesă e prea scurtă pentru tranzițiile alese, exportul eșuează cu un mesaj clar (fără reparare automată).
- Pasul 8c așteaptă încă ascultarea; acum mixul de test se poate asculta și întreg, din fișierul exportat.
