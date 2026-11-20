# Pasul 06 — Mixurile

## Ce am găsit înainte
`db/models.py` cu `Track`, `Waveform`, `energy_effective`; `api/tracks.py` cu `TrackOut` (refolosit
pentru piesele din mix); ecranul Mix-uri era doar un titlu. Decizii de dinainte: o piesă cel mult
o dată pe mix; ecranul Mix-uri = carduri + „Mix nou” (design.md).

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/db/models.py` + migrarea `0003` | schimbat/nou | `Mix`, `MixItem`, `EnergyShape` | `api/mixes.py`; raportul (7) |
| `backend/mixmatch/api/mixes.py`, `main.py` | nou/schimbat | CRUD + `PUT …/items` | `frontend/api/mixes.ts` |
| `backend/tests/test_api_mixes.py` (+ fixture-urile celorlalte teste API) | nou/schimbat | creare, ordine salvată, duplicate, ștergere, cascadă | `make test` |
| `frontend/package.json` | schimbat | dnd-kit | Constructorul |
| `frontend/src/api/mixes.ts` | nou | `useMixes`, `useMix`, creare, redenumire, ștergere, `useSetMixItems` (optimist) | ecranele de mix, Biblioteca |
| `frontend/src/features/mix-builder/{MixesScreen,MixBuilderScreen,MixTrackCard,AddTrackDialog,activeMixStore}.ts(x)` | noi | lista, Constructorul, cardul sortabil, adăugarea, mixul activ | `App.tsx`, Biblioteca |
| `frontend/src/features/library/{AddToMixButton,TrackPanel}.tsx` | nou/schimbat | „Adaugă în mix” în panou | Biblioteca |
| `frontend/src/App.tsx`, `ui/format.ts` (`formatMinutes`), `i18n/ro.ts` | schimbat | ruta `/mixuri/:mixId`, „43 min”, textele | — |

## Ce s-a făcut
- Ecranul Mix-uri: carduri (nume, „7 piese · 43 min”, „modificat 20 nov.”), „Mix nou”; gol → „Creează primul mix”.
- Constructorul: numele editabil (salvat la Enter sau la ieșirea din câmp), meta („4 piese · 14 min · 125 → 124 BPM”),
  cardurile din machetă (număr, mâner, copertă, titlu, artist, BPM · ton · E), scoatere (×), cardul „Adaugă”
  (dialog cu căutare), „Șterge mixul” cu confirmare.
- Reordonare prin drag: mouse, atingere și tastatură (spațiu, săgeți, spațiu), cu anunțuri în română.
- În Bibliotecă, panoul piesei are „Adaugă în „<mix>””, „Deja în „<mix>”” sau „Adaugă într-un mix nou”.

## Verificat în aplicația reală (Chrome, condus prin DevTools)
- 4 piese adăugate din Bibliotecă (prima a creat mixul) → lista arată „4 piese · 14 min”.
- Drag cu mouse-ul: cartea 4 → poziția 1. După reîncărcarea paginii, ordinea e aceeași.
- Tastatură: spațiu, săgeată dreapta, spațiu → prima carte trece pe poziția 2.
- Mixul de test a fost șters la final (`DELETE` → 204); baza ta nu are mixuri.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (dnd-kit, cheia și cascada din `mix_items`, API-ul,
  rutele, mixul activ, actualizările optimiste, dialogul de adăugare).

## Cum testezi
- `make lint && make test && make types` (203 teste backend, 35 frontend).
- `make dev` → Bibliotecă → selectează o piesă → „Adaugă într-un mix nou” → Mix-uri → deschide mixul
  → trage cardurile → reîncarcă pagina.

## Ce rămâne / atenție pentru pasul următor
- Pasul 7: `mixes/report.py` (etichetele dintre carduri, curba de energie, avertismentele),
  `PATCH` pentru `energy_shape`, segmented-ul Încălzire / Urcare / Val / Liber, panoul „Ce urmează după …”.
- Butoanele „Ordonează automat” (pasul 9) și „Ascultă mixul” nu sunt încă în antet.
