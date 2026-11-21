# mixmatch

Aplicație web locală pentru construit mixuri DJ din piesele tale: analiză automată
(tempo, ton, energie, grila de beat-uri), sugestii de piese compatibile, ordonare după o curbă
de energie, editor de tranziții cu ascultare și export (WAV/MP3, tracklist, .cue).

## Stadiu (2026-11-21)
- Pașii 0–11 din `docs/plan.md` sunt implementați; fiecare are nota lui în `docs/steps/`, iar
  deciziile sunt în `docs/decisions.md`. Pasul 12 (în afara planului) o mută pe server, în Docker
  (vezi „Pe server” mai jos).
- **Deschis:** criteriul pasului 8c (grila de beat-uri) cere confirmarea utilizatorului prin
  ascultare: cele 8 tranziții din mixul „Test beatmatch — ascultă tranzițiile” — care sunt pe beat
  fără corecție. Detalii în `docs/steps/08c-grila-de-beaturi.md`.
- **Opțional, în afara planului:** „Ascultă mixul” (redarea întregului mix în browser).
- Incidentul de după pasul 11 (migrarea 0008 a șters date în cascadă) e descris și reparat în
  `docs/steps/11-finisaje.md`.

## Pornire
Cerințe: Python ≥ 3.12, Node ≥ 20, ffmpeg (cu libmp3lame), git.

```
make setup   # o dată: mediul Python și pachetele Node
make dev     # backend pe 8000, interfața pe http://localhost:5173
make lint && make test && make types
```

## Pe server (unde rulează aplicația)
Aplicația rulează pe serverul de acasă `homebox` (192.168.2.140), în Docker:
**http://192.168.2.140:8090** (doar din rețeaua locală, fără autentificare).

| Ce | Pe server | În container |
| --- | --- | --- |
| Codul (clona git) + `compose.yaml` | `/opt/docker/compose/media/mixmatch` | — |
| Baza SQLite, cache-ul | `/opt/docker/appdata/mixmatch` (SSD) | `/data` |
| Muzica | `/srv/media/music` (RAID) | `/music` |
| Exporturile / importurile (drag & drop) | `/srv/media/music/mixmatch` / `…/Importate` | `/music/mixmatch` |

În aplicație, folderele bibliotecii se adaugă cu căile din container, de exemplu
`/music/House Set 1` pentru `/srv/media/music/House Set 1`.

```
ssh valeu@192.168.2.140
cd /opt/docker/compose/media/mixmatch
git pull && docker compose up -d --build   # actualizare (rulează și testele frontendului)
docker compose logs -f                     # jurnalul
docker build --target test .               # lint + testele backendului, în imagine
```
Prima instalare: folderele `/opt/docker/appdata/mixmatch` și `/srv/media/music/mixmatch/Importate` se
creează înainte (altfel Docker le face ca root), apoi `git clone` în folderul de mai sus și
`docker compose up -d --build`.

## Pe un calculator nou
Codul și documentația sunt în git; **datele nu**:
- `data/` (baza SQLite: biblioteca analizată, mixurile, tranzițiile, exporturile) e locală. Pe alt
  calculator pornești cu o bibliotecă goală: adaugi folderele cu muzică (căile sunt altele) și analiza
  rulează din nou. Mixurile se refac de mână. Poți copia `data/mixmatch.db` doar dacă muzica e la
  aceleași căi pe noul calculator.
- Exporturile se scriu în `~/Music/mixmatch/` (`MIXMATCH_EXPORT_DIR`), importurile prin drag & drop
  în `~/Music/mixmatch/Importate` (`MIXMATCH_UPLOAD_DIR`).
- Uneltele de evaluare din `backend/tools/` folosesc colecția Traktor (`collection.nml`) ca referință;
  fără Traktor, restul aplicației merge normal.

## Pentru o sesiune nouă de Claude Code
Primul mesaj:

> Citește CLAUDE.md, README.md și tot din docs/ (plan, decizii, design, toate notele de pas), apoi
> rezumă-mi scopul, arhitectura, ce e gata, ce e deschis și unde am rămas. Nu schimba nimic încă.

După aceea: „continuă cu …” (de exemplu confirmarea pasului 8c sau o funcție nouă).
