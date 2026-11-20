# mixmatch — plan de implementare

## 1. Scop

mixmatch e o aplicație web care rulează local și te ajută să construiești mixuri DJ din
piesele tale. Îți analizează automat biblioteca (tempo, ton, energie, formă de undă).
Îți arată ce piese merg bine una după alta, te ajută să ordonezi un set după o curbă
de energie și să ajustezi tranzițiile. La final exportă mixul.

Interfața trebuie să fie prietenoasă, minimală și ușor de folosit. Machetele din
`docs/design/` sunt ținta vizuală. Documentul acesta este ținta tehnică.

Fluxul principal: Import → Analiză → Alegi forma setului → Ordonezi (manual sau automat)
→ Ajustezi tranzițiile → Asculți → Exporți.

## 2. Principii (nu se negociază)

1. **Citește înainte să scrii.** Niciun fișier nou și nicio funcție nouă până nu ai citit
   modulele pe care le atinge pasul.
2. **O singură sursă de adevăr.** Modelul de date trăiește în backend. Tipurile din
   frontend se generează din schema OpenAPI.
3. **Logica muzicală stă într-un singur loc**: `backend/mixmatch/music/`.
4. **Fără cod orfan.** Un pas livrează doar ce folosește imediat. Un endpoint are un client
   care îl apelează, o componentă apare pe un ecran.
5. **Extinde, nu duplica.**
6. **Aplicația pornește după fiecare pas.** Testele trec, `make dev` merge.
7. **Deciziile se scriu** în `docs/decisions.md`, înainte de cod.

## 3. Arhitectura

Două părți care rulează local: un backend Python (analiză, date, export) și un frontend
React (interfață, redare).

| Strat | Alegere | De ce |
| --- | --- | --- |
| Backend | Python ≥ 3.12, FastAPI, Uvicorn | API rapid, OpenAPI generat automat |
| Analiză audio | Essentia (tempo, beat, ton, energie), librosa ca rezervă | Detectoare testate pe muzică electronică |
| Metadate | mutagen | Citește tag-urile din MP3, FLAC, WAV, AIFF |
| Date | SQLite + SQLAlchemy 2, migrări Alembic | Un singur fișier, nimic de instalat |
| Joburi | Coadă în proces (thread pool), starea în tabelul `jobs` | Analiza durează, dar nu justifică Redis |
| Export | ffmpeg | Randare WAV/MP3 |
| Frontend | Vite, React 18, TypeScript strict | Rapid local, tipuri stricte |
| Date în UI | TanStack Query + client generat cu `openapi-typescript` | Tipurile vin din backend |
| Stare UI | Zustand, doar pentru starea locală a interfeței | Datele serverului rămân în Query |
| Drag & drop | dnd-kit | Reordonarea pieselor în mix |
| Audio în UI | Web Audio API | Redare, crossfade, previzualizarea tranzițiilor |
| Teste | pytest, Vitest, Playwright (un singur flux cap-coadă) | Fiecare strat are testele lui |
| Lint | ruff (+ ruff format), eslint, prettier | Același stil peste tot |

```
frontend/features ──► frontend/api ──HTTP /api──► backend/api (rute FastAPI)
frontend/features ──► frontend/audio ──audio + planul tranziției──► backend/api
backend/api ──► library/ · analysis/ · music/ · mixes/ · export/
analysis/, mixes/, export/ ──► music/   (regulile muzicale stau doar aici)
backend ──► SQLite · fișierele audio (rămân în folderele lor) · ffmpeg
```

### Structura repo-ului

```text
mixmatch/
  CLAUDE.md
  Makefile               make setup · make dev · make test · make types · make lint
  docs/
    plan.md              acest document
    decisions.md         jurnalul de decizii
    design.md            culori, fonturi, componente, ecrane
    design/mockups/      sursa machetelor (referință vizuală, nu cod de producție)
    steps/               câte o notă la finalul fiecărui pas
  backend/
    pyproject.toml
    alembic/
    mixmatch/
      main.py            aplicația FastAPI, montează rutele
      config.py          setări (foldere, căi, versiunea analizei)
      jobs.py            coada de joburi
      api/               rute, câte un fișier pe resursă (health, library, tracks, mixes, jobs)
      db/                models.py, session.py
      library/           scan.py — scanare foldere, metadate, file_hash
      analysis/          tempo, beat, ton, energie, formă de undă
      music/             camelot.py, compat.py, transition_plan.py (singura sursă de reguli)
      mixes/             report.py, auto_order.py
      export/            render.py, tracklist, .cue
    tests/
  frontend/
    package.json
    src/
      main.tsx, App.tsx  shell-ul și rutarea
      api/               client generat (schema.d.ts) + hook-uri Query
      audio/             engine.ts — singurul loc cu AudioContext
      ui/                Button, Chip, KeyPill, EnergyDots, Waveform, TopBar, …
      features/
        library/         ecranul Biblioteca
        mix-builder/     ecranul Constructorul de mix
        transition/      ecranul Editorul de tranziție
        exports/         ecranul Exporturi
      theme/tokens.ts    culori, spațieri, raze
      i18n/ro.ts         textul interfeței
  test-tracks/           piese de test pentru pasul 3 (în .gitignore)
```

### Modelul de date

| Tabel | Câmpuri principale | Note |
| --- | --- | --- |
| `tracks` | id, path, file_hash, title, artist, duration_s, bpm, key_camelot, energy (1–5), energy_manual (1–5/null), first_beat_s, intro_bars, outro_bars, analysis_version, analyzed_at | `file_hash` evită reanaliza; `analysis_version` forțează reanaliza când se schimbă algoritmul |
| `waveforms` | track_id, peaks (blob, ~1000 puncte), peaks_hi (blob, ~8000 puncte) | Două rezoluții: listă și editor |
| `library_folders` | id, path, last_scan_at | Folderele urmărite |
| `collections`, `collection_tracks` | id, name · collection_id, track_id | Colecțiile din bara laterală (pasul 11) |
| `mixes` | id, name, energy_shape, created_at, updated_at | `energy_shape`: warmup, rise, wave, free |
| `mix_items` | mix_id, position, track_id | Ordinea pieselor |
| `transitions` | mix_id, from_track_id, to_track_id, length_bars, style, a_out_s, b_in_s | Legată de perechea A → B, nu de poziție: dacă perechea revine după o reordonare, setările revin. Dacă lipsește, se folosesc valori implicite calculate |
| `jobs` | id, kind, status, progress, error, created_at | Scanare, analiză, export |
| `exports` | id, mix_id, job_id, format, path, duration_s, created_at | Istoricul exporturilor pentru ecranul Exporturi (pasul 10b) |

### Contractul API (prefix `/api`)

| Metodă și rută | Ce face | Ecran |
| --- | --- | --- |
| `GET /health` | Verificare | — |
| `POST /library/folders` | Adaugă un folder și pornește scanarea | Biblioteca |
| `GET /jobs/{id}` | Progresul unui job | Toate |
| `GET /tracks` | Listă; filtre: bpm_min, bpm_max, energy, key (unul sau mai multe coduri Camelot), compatible_with, q, sort | Biblioteca |
| `PATCH /tracks/{id}` | Corecturi manuale (energy_manual) | Biblioteca |
| `GET /tracks/{id}/audio` | Fișierul audio, cu suport pentru Range | Toate |
| `GET /tracks/{id}/waveform?res=lo\|hi` | Vârfurile formei de undă | Biblioteca, Tranziție |
| `GET /tracks/{id}/matches` | Piese compatibile, cu scor și motiv în cuvinte | Biblioteca, Constructor |
| `GET/POST/PATCH/DELETE /mixes` | CRUD pentru mixuri; `GET /mixes` e lista (nume, număr de piese, durată, data) | Mix-uri, Constructor |
| `PUT /mixes/{id}/items` | Salvează ordinea pieselor | Constructor |
| `GET /mixes/{id}/report` | Eticheta fiecărei tranziții, curba de energie, avertismente | Constructor |
| `POST /mixes/{id}/auto-order` | Propune o ordine (nu o salvează) | Constructor |
| `GET /mixes/{id}/transitions/{pos}/plan` | Planul de automatizări al tranziției | Tranziție |
| `PATCH /mixes/{id}/transitions/{pos}` | Lungime, stil, puncte de intrare și ieșire | Tranziție |
| `POST /mixes/{id}/export` | Pornește randarea, întoarce un job | Exporturi |
| `GET /exports`, `GET /exports/{id}/file` | Lista exporturilor și descărcarea | Exporturi |

Importul în MVP înseamnă „adaugă un folder” (o cale de pe disc). Fișierele rămân unde
sunt. Drag & drop-ul cu upload vine în pasul 11.

### Reguli muzicale (implementate doar în `music/`)

- **Camelot**: 1A–12A (minor), 1B–12B (major). Compatibile: același cod; ±1 pe aceeași
  literă (ex. 8A → 7A, 9A; 12 → 1 face ocolul); aceeași cifră cu cealaltă literă (8A ↔ 8B).
  Diagonala (8A → 9B) contează ca „Bun”, nu „Lin”.
- **Tempo**: diferența în procente. Contează și jumătate/dublu (ex. 87 ↔ 174).
- **Sincronizarea tempo-ului în tranziție**: stil vinil. Piesa B se redă cu raportul
  `bpm_A / bpm_B` (viteza și tonul se schimbă împreună), fără time-stretch. Raportul face parte
  din planul tranziției; browserul îl aplică prin `playbackRate`, ffmpeg prin `asetrate` + `aresample`.
- **Etichete tranziții**: Lin / Bun / Atenție. Pragurile exacte se stabilesc în pasul 5 și
  se trec în `docs/decisions.md`.
- **Motivul în cuvinte**: fiecare scor vine cu un text scurt, de exemplu „8A → 9A · −1 BPM”.

## 4. Rutina fiecărui pas

1. **Citește**: fișierele din „Citește înainte”, `docs/decisions.md` și nota pasului anterior.
   Scrie în 3–5 rânduri ce ai înțeles.
2. **Planifică**: lista fișierelor care se schimbă sau apar, fiecare cu de ce și cine îl folosește.
3. **Implementează**: doar ce e în plan. Dacă apare nevoia de altceva, actualizezi întâi planul.
4. **Verifică**: `make lint`, `make test`, `make types` (fără diferențe neașteptate), apoi
   un test de mână al fluxului atins.
5. **Documentează**: `docs/steps/NN-nume.md`, apoi commit `step NN: <ce>`.

Convenții:
- Nume: Python `snake_case`, TypeScript `camelCase`, componente `PascalCase`.
- Unități: `_s` pentru secunde, `_bars` pentru bare, BPM cu o zecimală, ton în Camelot.
- Erori: `{"error": {"code", "message"}}`, afișate într-un singur toast global în frontend.
- Text UI: `frontend/src/i18n/ro.ts`. Stil: doar din `theme/tokens.ts`.

## 5. Pașii

Pașii 0–7 formează MVP-ul: bibliotecă analizată, mix ordonat, avertismente pentru tranziții.
Pașii 3, 8 și 10 se fac în două prompturi (a/b).

### Pasul 0 — Scheletul
- **Scop**: repo-ul, uneltele și un ecran gol care arată ca macheta.
- **Citește înainte**: `docs/plan.md`, `docs/design.md`, machetele.
- **Livrează**: structura de foldere; `Makefile` (`setup` verifică Python ≥ 3.12, Node ≥ 20,
  ffmpeg; `dev` pornește backendul pe 8000 și Vite pe 5173 cu proxy `/api`; `test`, `lint`,
  `types`); `backend/pyproject.toml`; FastAPI cu `GET /api/health`; Vite + React + TS strict;
  `theme/tokens.ts` cu valorile din `docs/design.md`; `i18n/ro.ts`; componenta `TopBar` din
  machetă cu navigarea Bibliotecă / Mix-uri / Exporturi (ecrane goale); ruff, eslint, prettier;
  `.gitignore`.
- **Gata când**: `make dev` deschide bara de sus în stilul machetei, iar frontendul afișează
  starea `/api/health`.

### Pasul 1 — Baza de date
- **Scop**: tabelele `tracks`, `library_folders`, `jobs` și prima migrare.
- **Citește înainte**: `config.py`, `main.py`, `api/health.py`.
- **Livrează**: `db/models.py`, `db/session.py`, configurarea Alembic și prima migrare, `jobs.py`.
- **Gata când**: migrarea rulează pe o bază goală, iar testele pentru modele și joburi trec.

### Pasul 2 — Scanarea bibliotecii
- **Scop**: adaugi un folder și vezi piesele în tabel (titlu, artist, durată).
- **Citește înainte**: `db/models.py`, `jobs.py`, `features/`, `ui/`.
- **Livrează**: `library/scan.py` (formate: MP3, FLAC, WAV, AIFF, M4A; fișierele sub 60 s se ignoră,
  pragul e în `config.py`); `POST /library/folders`, `GET /jobs/{id}`, `GET /tracks`;
  primul `make types` și hook-urile din `api/`; ecranul Biblioteca cu tabelul și dialogul
  „Adaugă folder” cu progres.
- **Gata când**: un folder cu 50 de piese apare complet, iar o rescanare nu creează duplicate.

### Pasul 3a — Analiza: tempo, beat, ton
- **Scop**: BPM, primul beat și tonul în Camelot pentru fiecare piesă.
- **Citește înainte**: `library/scan.py`, `jobs.py`, `db/models.py`.
- **Livrează**: `analysis/tempo.py`, `analysis/key.py`, `music/camelot.py` (conversia ton → Camelot,
  numele clasic), analiza pornită automat după scanare, `analysis_version`; coloanele BPM și Ton
  în tabel, cu `KeyPill`.
- **Gata când**: comparat cu piesele din `test-tracks/` (tempo și ton cunoscute), cu acuratețea
  notată în nota pasului.

### Pasul 3b — Analiza: energie, formă de undă, intro/outro
- **Scop**: energia 1–5, vârfurile formei de undă, lungimea intro-ului și a outro-ului.
- **Citește înainte**: `analysis/`, nota pasului 3a.
- **Livrează**: `analysis/energy.py`, `analysis/waveform.py`, tabelul `waveforms`,
  `GET /tracks/{id}/waveform`, `PATCH /tracks/{id}` (energy_manual); `EnergyDots` și `Waveform`
  în `ui/`; corectarea manuală a energiei în UI.
- **Gata când**: tabelul arată ca macheta Biblioteca, iar energia corectată de mână are prioritate.

### Pasul 4 — Redarea
- **Scop**: butonul de play din tabel și panoul „Selectată”.
- **Citește înainte**: `api/tracks.py`, `ui/Waveform`, `features/library/`.
- **Livrează**: `GET /tracks/{id}/audio` cu Range; `audio/engine.ts` (un singur player în toată
  aplicația); panoul din dreapta (date despre piesă, forma de undă mare).
- **Gata când**: poți asculta și derula orice piesă, iar două piese nu cântă niciodată simultan.

### Pasul 5 — Compatibilitatea și filtrele
- **Scop**: „Merg bine după ea” și filtrele din bara laterală.
- **Citește înainte**: `music/camelot.py`, `api/tracks.py`, panoul din dreapta.
- **Livrează**: `music/compat.py` (scor din ton, diferența de tempo în %, saltul de energie, plus
  motivul în cuvinte; pragurile Lin/Bun/Atenție trecute în decisions); `GET /tracks/{id}/matches`;
  filtrele din `GET /tracks`; bara laterală cu filtre.
- **Gata când**: testele acoperă toate relațiile de pe roata Camelot, iar UI-ul nu conține
  nicio regulă de compatibilitate.

### Pasul 6 — Mixurile
- **Scop**: creezi un mix, adaugi piese din bibliotecă, le reordonezi prin drag.
- **Citește înainte**: `db/models.py`, `api/`, `features/library/`.
- **Livrează**: tabelele `mixes` și `mix_items` (migrare), CRUD și `PUT /mixes/{id}/items`;
  ecranul Mix-uri (lista de mixuri ca carduri, „Mix nou”); ecranul Constructorul de mix
  (cardurile, cu dnd-kit); „Adaugă în mix” din bibliotecă.
- **Gata când**: ordinea rămâne salvată după refresh.

### Pasul 7 — Raportul mixului
- **Scop**: etichetele Lin / Bun / Atenție, curba de energie și avertismentele.
- **Citește înainte**: `music/compat.py`, `api/mixes.py`, ecranul Constructor.
- **Livrează**: `mixes/report.py` (folosește `compat.py`, nu îl copiază); `GET /mixes/{id}/report`;
  curba de energie cu forma aleasă (Încălzire / Urcare / Val / Liber); bannerul de avertismente;
  panoul de sugestii (refolosește `/matches`).
- **Gata când**: schimbi ordinea și etichetele se actualizează imediat.

### Pasul 8a — Editorul de tranziție: planul și ecranul
- **Scop**: tranziția descrisă ca plan și ecranul în care o editezi.
- **Citește înainte**: `analysis/` (beat grid, intro, outro), `mixes/report.py`, ecranul Constructor.
- **Livrează**: tabelul `transitions` (migrare); `music/transition_plan.py` (lungime în bare aliniată
  la fraze; stilurile eq_swap, crossfade, echo_out, cut; ieșirea e raportul de viteză al lui B plus o
  listă de automatizări în secunde, pentru volum, EQ de bas și ecou pe fiecare deck); `GET .../plan`, `PATCH .../transitions/{pos}`;
  ecranul Tranziție (cele două forme de undă suprapuse, lungime, stil).
- **Gata când**: când schimbi lungimea sau stilul, planul și desenul se actualizează.

### Pasul 8b — Editorul de tranziție: redarea planului
- **Scop**: „Ascultă tranziția”.
- **Citește înainte**: `audio/engine.ts`, `music/transition_plan.py`, ecranul Tranziție.
- **Livrează**: `audio/engine.ts` execută planul (două surse, GainNode, BiquadFilter, DelayNode),
  redând doar fereastra tranziției.
- **Gata când**: ce auzi e generat exclusiv din planul primit de la backend.

### Pasul 9 — Ordonarea automată
- **Scop**: butonul „Ordonează automat”.
- **Citește înainte**: `music/compat.py`, `mixes/report.py`.
- **Livrează**: `mixes/auto_order.py` (același scor ca raportul, plus abaterea de la curba de
  energie; greedy + căutare locală); `POST /mixes/{id}/auto-order`; o previzualizare în UI pe
  care o accepți sau o refuzi.
- **Gata când**: ordinea propusă are un scor total mai bun sau egal cu ordinea ta.

### Pasul 10a — Exportul: randarea
- **Scop**: mixul ca fișier WAV/MP3.
- **Citește înainte**: `music/transition_plan.py`, `jobs.py`, `audio/engine.ts`.
- **Livrează**: `export/render.py`: ffmpeg execută aceleași planuri (filtre volume, equalizer,
  aecho, sincronizare tempo stil vinil cu asetrate + aresample); `POST /mixes/{id}/export` ca job.
- **Gata când**: exportul sună la fel ca previzualizarea, verificat pe trei tranziții.

### Pasul 10b — Exportul: tracklist, .cue, ecranul
- **Scop**: tracklistul cu timpi, fișierul .cue și ecranul Exporturi.
- **Citește înainte**: `export/render.py`, `features/`.
- **Livrează**: tabelul `exports` (migrare); tracklistul (text), fișierul .cue; `GET /exports`,
  `GET /exports/{id}/file`; ecranul Exporturi (lista exporturilor, progresul, descărcarea).
- **Gata când**: timpii din tracklist corespund cu fișierul randat.

### Pasul 11 — Finisaje
- **Scop**: lucrurile din machete rămase în afara MVP-ului.
- **Livrează**: drag & drop cu upload într-un folder administrat, colecții și tag-uri, stări goale,
  scurtături de tastatură.
- **Gata când**: fiecare funcție are nota ei în `docs/steps/` și apare în cel puțin un ecran.

## 6. Decizii deschise
- **Piesele de test** (rezolvat): ~20 de piese din `~/Music`, alese din genuri diferite, cu BPM-ul
  și tonul din colecția Traktor 4 a utilizatorului ca referință. Lista (cale, BPM, Camelot) stă
  în `test-tracks/` (care nu intră în git); fișierele audio nu se copiază. Valorile Traktor sunt
  tot o estimare, deci pasul 3a măsoară acordul cu Traktor (cu toleranță pentru jumătate/dublu la
  tempo și pentru tonul relativ), nu adevărul absolut.
- **Formatele de export** (rezolvat): doar audio (WAV/MP3), tracklist și .cue. Rekordbox XML și
  Serato rămân după MVP.
- **Licența Essentia (AGPL)**: pentru uz personal nu e o problemă. Se revizuiește doar dacă
  aplicația devine publică.
