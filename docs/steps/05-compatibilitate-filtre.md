# Pasul 05 — Compatibilitatea și filtrele

## Ce am găsit înainte
`music/camelot.py` (conversie, `parse`, nume clasic), `api/tracks.py` cu lista fără filtre,
`Track.energy_effective` (hybrid, merge și în SQL), panoul „Selectată” fără sugestii. Deciziile
de dinainte: tempo Lin ≤ 3 %, Bun ≤ 6 %; tonul se judecă după transpunerea stil vinil.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/music/camelot.py` | schimbat | `shift` (transpunere pe roată) | `compat.py` |
| `backend/mixmatch/music/compat.py` | nou | eticheta, scorul, motivul, viteza și tonul după sincronizare | `api/tracks.py`; raportul (7), ordonarea (9), tranziția (8a) |
| `backend/mixmatch/api/tracks.py` | schimbat | filtrele `GET /tracks`, `GET /tracks/{id}/matches` | Biblioteca |
| `backend/tests/test_compat.py`, `test_api_filters.py` | noi | toate perechile de pe roată (576), pragurile, transpunerea, filtrele | `make test` |
| `frontend/src/api/tracks.ts` | schimbat | `TrackFilters`, `useTracks(filters)`, `useMatches` | Biblioteca |
| `frontend/src/ui/TransitionTag.tsx` | nou | Lin / Bun / Atenție, cu formă și culoare | sugestii; constructorul (6–7) |
| `frontend/src/ui/TopBar.tsx`, `App.tsx` | schimbat | slot pentru căutare | — |
| `frontend/src/features/library/{filterStore,Sidebar,LibrarySearch,MatchList}.ts(x)` | noi | filtrele, bara laterală, căutarea, „Merg bine după ea” | `LibraryScreen`, `TrackPanel` |
| `frontend/src/features/library/{LibraryScreen,TrackPanel}.tsx`, `i18n/ro.ts` | schimbat | trei coloane, sortarea, mesajul „niciun rezultat” | — |

## Ce s-a făcut
- `music/compat.py` e singurul loc cu reguli: B se sincronizează la A (cu jumătate/dublu), tonul
  lui B se transpune la viteza nouă, apoi ton + tempo + energie dau eticheta; scorul ordonează.
- Panoul arată „Merg bine după ea” (titlu, motiv, eticheta); click pe o sugestie o selectează.
- Bara laterală: tempo min/max, energie 1–5, tonuri (grilă de 24), „Doar compatibile cu …”,
  „Șterge filtrele”, nota despre analiza locală. Sortare în antet, căutare în bara de sus.
- UI-ul nu conține nicio regulă de compatibilitate: doar trimite filtrele și afișează.

## Verificat pe biblioteca reală
- `/matches` răspunde în 5–8 ms pe 246 de piese; exemple: „Get Over It” (124, 4A, E2) →
  Chunky, Cola, Morenita (4A → 3A), toate Lin.
- Găsite și reparate pe date reale: același fișier în două foldere apărea de două ori în sugestii
  (acum o copie per `file_hash`); un „Bun” cu scor 92 trecea înaintea unui „Lin” cu 92 (acum Lin întâi).
- În Chrome: compatibile cu „Get Over It” → 78; plus energie 2 → 23; căutarea „remix” → 44.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (roata, transpunerea, energia, eticheta și scorul,
  ordinea sugestiilor, filtrele, „compatibile cu” după piesă, motivul în backend).

## Cum testezi
- `make lint && make test && make types` (194 de teste backend, 24 frontend).
- `make dev` → selectează o piesă → „Merg bine după ea”; bifează „Doar compatibile cu …”; combină cu energie și ton.

## Ce rămâne / atenție pentru pasul următor
- Pasul 6: mixurile (tabelele `mixes`, `mix_items` cu piesă unică pe mix), ecranul Mix-uri,
  Constructorul cu dnd-kit, „Adaugă în mix” în panou.
- Tabelul are acum trei coloane alături; sub ~1440 px lățime, forma de undă se derulează orizontal.
- În VS Code, pylint arată „Unable to import fastapi”: editorul nu folosește `backend/.venv`
  (Python: Select Interpreter → `backend/.venv/bin/python`). Proiectul folosește ruff.
