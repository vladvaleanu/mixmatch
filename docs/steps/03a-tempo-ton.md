# Pasul 03a — Analiza: tempo, beat, ton

## Ce am găsit înainte
`library/scan.py` scanează și face upsert după cale; `jobs.py` rulează funcții cu `report(progress)`
într-un thread pool; `Track` avea deja coloanele `bpm`, `key_camelot`, `first_beat_s`,
`analysis_version`, `analyzed_at`. Scanarea pornea din `api/library.py`. În frontend, tabelul avea
doar Piesă și Durată, iar `useJob` urmărea doar jobul scanării.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/pyproject.toml` | schimbat | essentia | analiza |
| `backend/mixmatch/config.py` | schimbat | `analysis_version = 1`, `analysis_workers` | `analysis/runner.py` |
| `backend/mixmatch/music/camelot.py` | nou | ton → Camelot, numele clasic, `parse` | `analysis/key.py`, `api/tracks.py`, unealta de evaluare |
| `backend/mixmatch/analysis/audio.py` | nou | citire mono 44,1 kHz | `track.py` |
| `backend/mixmatch/analysis/tempo.py`, `key.py` | noi | detectoarele Essentia | `track.py` |
| `backend/mixmatch/analysis/track.py` | nou | `analyze_file` (rulează în procese separate) | `runner.py`, unealta de evaluare |
| `backend/mixmatch/analysis/runner.py` | nou | jobul de analiză, `start_analysis_if_needed` | `api/library.py`, `main.py` |
| `backend/mixmatch/library/scan.py` | schimbat | fișier schimbat → `analysis_version = None` | scanarea |
| `backend/mixmatch/api/library.py`, `main.py` | schimbat | analiza după scanare și la pornire | — |
| `backend/mixmatch/api/jobs.py` | schimbat | `GET /jobs/active` | `frontend/api/jobs.ts` |
| `backend/mixmatch/api/tracks.py` | schimbat | `bpm`, `key_camelot`, `key_name`, `analyzed` | tabelul |
| `backend/tools/evaluate_analysis.py` | nou | alege piesele de test din Traktor și măsoară acordul | acest pas, pașii care schimbă analiza |
| `backend/tests/audio.py` (`make_music`), `test_camelot.py`, `test_analysis.py`, `test_api_library.py` | noi/schimbat | piese sintetice cu tempo și ton cunoscute; testele pasului | `make test` |
| `frontend/src/theme/tokens.ts` | schimbat | `keyColor`, `coverColor` (formula din design.md) | `KeyPill`, tabelul |
| `frontend/src/ui/KeyPill.tsx`, `format.ts` (`formatBpm`) | nou/schimbat | pastila tonului, BPM afișat | tabelul |
| `frontend/src/api/jobs.ts` | schimbat | `useActiveJobs` | `AnalysisBanner` |
| `frontend/src/features/library/AnalysisBanner.tsx` | nou | progresul analizei; reîncarcă tabelul | `LibraryScreen` |
| `frontend/src/features/library/{TrackTable,LibraryScreen,AddFolderDialog}.tsx`, `i18n/ro.ts` | schimbat | coperta, BPM, Ton; mesajul „analiza continuă în fundal” | — |

## Ce s-a făcut
- După fiecare scanare (și la pornirea serverului) pornește un job de analiză pentru piesele noi,
  schimbate sau analizate cu o versiune veche. Rulează în paralel, în procese separate.
- Tabelul arată coperta în culoarea tonului, BPM-ul și `KeyPill` (numele clasic apare la hover).
  Piesele în așteptare au „…”. Deasupra tabelului apare progresul analizei.

## Acuratețea (față de Traktor 4, pe biblioteca utilizatorului)
Piesele de referință: `test-tracks/reference.csv`, 20 de piese din 15 foldere din `~/Music`
(9 WAV, 7 M4A, 2 MP3, 2 FLAC). Traktor e tot o estimare, deci e acord, nu adevăr absolut.

| Set | Tempo exact (±0,5) | Tempo dublu/jumătate | Ton exact | Ton vecin (cvintă/relativ) | Ton greșit |
| --- | --- | --- | --- | --- | --- |
| 20 de piese de referință | 17/20 | 0/20 | 10/20 | 6/20 | 4/20 |
| 80 de piese aleatorii | 69/80 | 6/80 | 54/80 | 14/80 | 12/80 |

- Erorile de tempo: un hip-hop la 87,6 citit 172,3 (dublu, dar și cu ~1 BPM diferență), un snippet
  de 64 BPM și o piesă din 1996 (125 citit 123,9).
- Profilul de ton ales e `bgate`; comparația pe 100 de piese e în `docs/decisions.md`.
- Pe piese sintetice, Essentia are pași de rezoluție la tempo mare (174 → 172,3; 128 → 128,7).

## Verificat pe biblioteca reală
- La pornire, analiza a luat singură cele 246 de piese scanate în pasul 2: toate analizate,
  niciun eșec, în ~3,5 min cu 4 procese. Limita a crescut apoi la 6 procese.
- Bug găsit și reparat: SQLite refolosește id-urile șterse, iar un rezultat al analizei putea
  ajunge pe altă piesă dacă o rescanare ștergea și adăuga piese între timp. Acum se verifică și calea.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (essentia, tempo fără rafinare, profilul `bgate`,
  procese paralele, analizele eșuate, verificarea căii, `GET /jobs/active`, formatul BPM).

## Cum testezi
- `make lint && make test && make types` (89 de teste backend, 13 frontend).
- `make dev`: piesele neanalizate se analizează singure; „Importă piese” → la final pornește analiza.
- Acuratețea: `backend/.venv/bin/python backend/tools/evaluate_analysis.py run` (~80 s).
- Alte piese de test: `… evaluate_analysis.py pick "~/Documents/Native Instruments/Traktor 4.0.2/collection.nml"`.

## Ce rămâne / atenție pentru pasul următor
- **Grila de beat-uri** (`first_beat_s`) moștenește eroarea de tempo: pe sintetic, la 174 BPM primul
  beat iese decalat cu ~0,15 s. Pentru house/techno (120–145) a fost exact. Pasul 8a, care aliniază
  tranzițiile pe beat-uri, trebuie să verifice alinierea pe piese reale; poate fi nevoie de rafinarea
  locală a grilei.
- Erori dublu/jumătate (6/80): compatibilitatea (pasul 5) trebuie să trateze 87 ↔ 174, cum zice planul.
- Fereastra mică de concurență: dacă o scanare se termină exact când analiza își încheie ultima tură,
  piesele noi rămân neanalizate până la următoarea scanare sau pornire.
- Pasul 3b: energie, formă de undă, intro/outro. Crește `analysis_version` la 2, ca toate piesele
  să primească și valorile noi.
