# Pasul 08c — Grila de beat-uri

## Ce am găsit înainte
Analiza păstra doar BPM-ul global și primul beat; planul extrapola punctele pe sute de beat-uri.
Nota pasului 8b: pe 7 tranziții reale, kick-urile lui A și B nu cădeau împreună; măsurătoarea
automată între perechi de piese era ambiguă. Decizia utilizatorului: corecție manuală (`b_nudge_s`)
în 8b, grila automată în acest pas, validată prin ascultare.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/tools/evaluate_beatgrid.py` | nou | grila noastră față de AutoGrid-urile Traktor (referință per piesă) | acest pas, viitoarele schimbări de analiză |
| `backend/mixmatch/analysis/tempo.py` | rescris | `detect_beats`: toate beat-urile + corecția de contratimp pe kick | `analysis/track.py`, unealta |
| `backend/mixmatch/analysis/track.py`, `runner.py`, `config.py` | schimbat | beat-urile în rezultat, salvate în `beat_grids`; `analysis_version = 5` | analiza |
| `backend/mixmatch/db/models.py` + migrarea `0006` | schimbat/nou | tabelul `beat_grids` | analiza, planul |
| `backend/mixmatch/music/transition_plan.py` | schimbat | `on_beat`, `local_beat_s`, `_local_sync`; `Side.beats` | API |
| `backend/mixmatch/api/transitions.py` | schimbat | încarcă grila piesei în `Side` | planul |
| `backend/tests/test_beat_grid.py`, `test_analysis.py` | nou/schimbat | contratimp, puncte pe beat-uri reale, tempo local, salvarea grilei | `make test` |

## Măsurători
- **Față de Traktor** (80 de piese aleatorii din `~/Music`, `evaluate_beatgrid.py 80`), înainte → după:
  pe beat (±15 ms) 20–22 → 35–40; pe contratimp 33–34 → 13–14; restul sunt decalaje mici, multe
  la ±15–40 ms (iar MP3 e decalat ~30 ms față de Traktor din cauza decodării, nu a grilei).
- Am încercat și: poziția kick-ului ca fază (întârzie sistematic ~50 ms, prea împrăștiată), corecții
  constante (strică: tendința reală e doar −8 ms). Rămâne grila Essentia + decizia de ½ beat.
- Pe mixul de test, măsurătoarea între perechi rămâne neclară (vârfuri slabe); de aceea criteriul e ascultarea.

## Starea criteriului „Gata când”
Neconfirmat încă: utilizatorul ascultă cele 8 tranziții din „Test beatmatch — ascultă tranzițiile”
(http://localhost:5173/mixuri/1) și spune care sunt pe beat. `b_nudge_s` rămâne pentru excepții.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (grila cu corecția de contratimp, punctele pe beat-uri
  și tempo-ul local, unealta de evaluare).

## Cum testezi
- `make lint && make test && make types` (252 de teste backend, 54 frontend).
- `cd backend && .venv/bin/python tools/evaluate_beatgrid.py 80` (~1 min).
- Ascultare: `make dev` → Mix-uri → „Test beatmatch” → click pe etichetele dintre carduri → „Ascultă tranziția”.

## Ce rămâne / atenție pentru pasul următor
- ~15 % din piese au rămas pe contratimp: decizia pe kick greșește când basul de pe contratimp e mai tare
  decât kick-ul în 40–100 Hz. Dacă ascultarea confirmă problema, următoarea îmbunătățire e o detecție de
  kick mai specifică (atacul scurt, nu nivelul).
