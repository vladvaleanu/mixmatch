# Pasul 08b — Editorul de tranziție: redarea planului

## Ce am găsit înainte
`music/transition_plan.py` (planul: puncte, viteză, câștiguri, automatizări de volum/bas/ecou),
ecranul Tranziție (desen, lungime, stil, puncte), `audio/engine.ts` cu un singur `<audio>` pentru
redarea pieselor. Ecoul era descris ca întârziere + feedback, fără fereastră de ascultat.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/music/transition_plan.py` | schimbat | `echo_taps`, `bass_shelf_hz`, fereastra de previzualizare | browserul; ffmpeg (10a) |
| `backend/mixmatch/library/playback.py`, `api/tracks.py` | schimbat | `render_clip`, `GET /tracks/{id}/clip` | previzualizarea |
| `backend/mixmatch/analysis/audio.py`, `config.py` | schimbat | decodare cu ffmpeg; `analysis_version = 4` | analiza |
| `backend/mixmatch/api/transitions.py` | schimbat | câmpurile noi din plan | ecranul |
| `backend/tests/conftest.py` + testele API, `test_jobs.py`, `test_transition_plan.py`, `test_api_playback.py` | schimbat | fixture comun; cursa din testele de joburi; ecou, fereastră, bucăți | `make test` |
| `frontend/src/audio/plan.ts` | nou | `valueAt`, `clipRanges` (citirea planului) | `transition.ts`, desenul |
| `frontend/src/audio/transition.ts` | nou | graful Web Audio programat din plan | `engine.ts`; teste offline |
| `frontend/src/audio/engine.ts` | schimbat | `transitionPreview` (play/stop, cursor), regula „un singur lucru se aude” | ecranul Tranziție |
| `frontend/src/audio/fakeAudio.ts`, `transition.test.ts`, `engine.test.ts` | nou/schimbat | context audio fals: verifică ce se programează | `make test` |
| `frontend/src/api/tracks.ts` | schimbat | `fetchClip` | ecranul Tranziție |
| `frontend/src/features/transition/{TransitionScreen,TransitionView}.tsx` | schimbat | „Ascultă tranziția”, cursorul; `valueAt` din `audio/plan.ts` | — |

## Ce s-a făcut
- „Ascultă tranziția” cântă fereastra tranziției (4 bare înainte, tranziția, 4 bare după).
- Graful, pe fiecare deck: sursă (viteza din plan) → low-shelf (basul din plan) → volum (automatizarea × auto-gain);
  A trimite după filtru în ecou (6 copii întârziate), direct la ieșire. Toate valorile și momentele vin din plan.
- Testele cu context audio fals verifică exact ce se programează: momentele de start, viteza, rampele de volum
  cu auto-gain, saltul de bas, ecoul. Previzualizarea oprește playerul și invers.

## Verificat în aplicația reală
- Chrome: „Ascultă tranziția” → bucățile se încarcă în < 0,3 s, cursorul avansează, „Oprește” revine la repaus.
- Randare offline în Chrome cu codul din `audio/transition.ts`: aceeași piesă pe ambele deck-uri iese
  aliniată la 0 ms; decalată intenționat cu 40 ms, măsurătoarea arată −40 ms. Execuția planului e exactă.
- **Găsit și reparat:** analiza (decodorul Essentia) și bucățile (ffmpeg) aveau cronologii diferite cu
  ~36–46 ms la M4A (amorsarea AAC). Analiza decodează acum tot cu ffmpeg; diferența a scăzut la ±20 ms
  (zgomotul măsurătorii). Biblioteca s-a reanalizat singură (versiunea 4).

## Problemă deschisă: beat-urile dintre piese diferite
Pe 7 tranziții reale (122–124 BPM), kick-urile lui A și B **nu cad împreună** în majoritatea cazurilor.
Ce am aflat:
- Grila Essentia nu stă mereu pe kick: la unele piese stă pe contratimp (jumătate de beat decalat), iar
  decalajul variază de la piesă la piesă.
- Punctul de ieșire e extrapolat din BPM pe sute de beat-uri: o eroare mică de tempo devine ~100 ms la final.
- Măsurătoarea automată pe perechi diferite e ambiguă (modele de kick/bas diferite în intro/outro), deci
  nu poate valida singură o corecție. Am încercat beat-uri locale, corecție de fază pe kick și corecție de
  jumătate de beat: niciuna nu a dat rezultate clare.
Decizia utilizatorului: corecție manuală acum (`b_nudge_s`, butoanele „Potrivirea beat-urilor” din
editor: −½ beat, −10 ms, +10 ms, +½ beat, 0), iar grila automată devine pasul 8c, validat prin
ascultare. Pentru ascultare există în bază un mix de test („Test beatmatch — ascultă tranzițiile”).

## Decizii
- Vezi primele intrări din `docs/decisions.md` (bucăți decupate de ffmpeg, ecoul multi-tap, fereastra în plan,
  decodarea analizei cu ffmpeg, „un singur lucru se aude”, fixture-ul comun).

## Cum testezi
- `make lint && make test && make types` (246 de teste backend, 54 frontend).
- `make dev` → un mix → o tranziție → „Ascultă tranziția”; schimbă stilul și ascultă din nou.

## Ce rămâne / atenție pentru pasul următor
- Alinierea beat-urilor între piese (vezi mai sus).
- Pasul 10a: exportul cu ffmpeg trebuie să execute același plan: low-shelf la `bass_shelf_hz`, `echo_taps` ca
  sumă de întârzieri, volumul ca automatizare liniară, viteza B prin `asetrate` + `aresample`.
- Limiter-ul decis pentru export nu există în previzualizare; de decis la 10a dacă intră și în browser.
