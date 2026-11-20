# Pasul 09 — Ordonarea automată

## Ce am găsit înainte
`music/compat.py` (scorul și eticheta unei perechi, `CURVE_PENALTY` pentru sugestii),
`music/energy_curve.py` (curbele), `mixes/report.py` (etichetele unei ordini), Constructorul cu
`useSetMixItems`. Decizie de dinainte: prima piesă rămâne pe loc.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/music/compat.py` | schimbat | `pair_value`, `curve_cost`, `CAUTION_PENALTY` | ordonarea |
| `backend/mixmatch/mixes/auto_order.py` | nou | greedy + căutare locală; „niciodată mai slab” | `api/mixes.py` |
| `backend/mixmatch/api/mixes.py` | schimbat | `POST /mixes/{id}/auto-order` | Constructorul |
| `backend/tests/test_auto_order.py`, `test_api_mixes.py` | nou/schimbat | 120 de mixuri aleatorii (scor ≥, prima fixă), roata, curba, API fără salvare | `make test` |
| `frontend/src/api/mixes.ts` | schimbat | `useAutoOrder` | Constructorul |
| `frontend/src/features/mix-builder/{AutoOrderDialog,MixBuilderScreen}.tsx`, `i18n/ro.ts` | nou/schimbat | butonul din antet, previzualizarea (Acceptă / Renunță) | — |

## Ce s-a făcut
- „Ordonează automat” (dezactivat sub 3 piese) → dialogul „Ordinea propusă”: lista cu etichetele dintre
  piese, „Tranziții Atenție: 2 → 0” și „Tranziții Lin: 2 → 8”; „Acceptă” salvează, „Renunță” lasă ordinea.
- Dacă ordinea ta e deja cea mai bună: „Ordinea ta e deja cea mai bună pe care am găsit-o.”

## Verificat în aplicația reală
- Mix temporar de 12 piese aleatorii (120–128 BPM), forma „Urcare”: scor 481 → 893, Atenție 2 → 0,
  Lin 2 → 8, în 6 ms; în Chrome, după „Acceptă”, etichetele dintre carduri arată noua ordine. Mixul a fost șters.
- Energia nu urcă până la 5 pentru că mixul nu are piese de energie 5; ponderi mai mari ale curbei au adus
  puțin (abatere 12 → 10) și au costat o tranziție „Lin”.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (scorul unei ordini, algoritmul, API-ul, ponderea curbei).

## Cum testezi
- `make lint && make test && make types` (379 de teste backend, 56 frontend).
- `make dev` → un mix cu piese amestecate → „Ordonează automat” → Acceptă.

## Ce rămâne / atenție pentru pasul următor
- Pasul 8c așteaptă încă confirmarea prin ascultare (mixul „Test beatmatch”).
- „Ce urmează după …” poate arăta aceeași piesă în versiuni diferite („… Mix” și „… Extended Mix”): sunt fișiere
  diferite, deci deduplicarea după conținut nu le prinde.
- Pasul 10a: exportul cu ffmpeg, din aceleași planuri.
