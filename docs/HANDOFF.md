# HANDOFF — fișier TEMPORAR de migrare

> **Temporar.** Fișierul ăsta și blocul „MIGRARE TEMPORARĂ” din `CLAUDE.md` există doar ca o nouă
> instanță de Claude Code, pe alt calculator, să preia lucrul cu tot contextul conversației de pe Mac.
> La final se șterg amândouă (vezi „Pasul 4” mai jos). Nu le referi din alte fișiere.

Scris pe 2026-11-21 de instanța care a construit proiectul (pașii 0–11), la cererea utilizatorului.

---

## 1. Instrucțiuni de migrare (pentru noua instanță)

### Pasul 1 — Citește
1. Acest fișier, integral.
2. `CLAUDE.md`, `README.md`, `docs/plan.md`, `docs/decisions.md` (sus = cele mai noi), `docs/design.md`.
3. Toate notele din `docs/steps/`, în ordine (00 → 11). Notele 08b, 08c, 10a, 11 conțin măsurători și
   incidente importante.

### Pasul 2 — Pregătește mediul
- Cerințe: Python ≥ 3.12, Node ≥ 20, ffmpeg cu libmp3lame, git. Pe Windows: WSL (Makefile-ul presupune
  un shell Unix). Atenție: pe Mac-ul vechi `python3` era 3.11; Makefile-ul caută explicit `python3.12`/`3.13`.
- `make setup`, apoi `make lint && make test && make types` — totul trebuie să treacă (la predare:
  404 teste backend, 67 frontend).
- `make dev` → http://localhost:5173. Prima pornire creează `data/mixmatch.db` gol (biblioteca nu vine prin git).

### Pasul 3 — Confirmă cu utilizatorul
Rezumă-i în câteva rânduri: scopul, arhitectura, ce e gata, ce e deschis (secțiunea 3) și ce nu s-a mutat
(datele locale, secțiunea 5). Întreabă-l dacă vrea să adauge folderele cu muzică pe calculatorul nou.
Nu începe muncă nouă înainte de confirmare.

### Pasul 4 — Curățenia (după ce utilizatorul confirmă că migrarea e gata)
1. Șterge `docs/HANDOFF.md`.
2. Șterge din `CLAUDE.md` blocul dintre `<!-- MIGRARE TEMPORARĂ -->` și `<!-- /MIGRARE TEMPORARĂ -->`
   (inclusiv marcajele).
3. Dacă vreo informație de aici trebuie păstrată, mut-o întâi în locul ei permanent (notă de pas,
   `decisions.md`, README) — nu păstra fișierul.
4. `make lint && make test` trec, apoi commit „docs: șterge fișierele temporare de migrare” și push.

---

## 2. Cum lucrează utilizatorul (preferințe confirmate în conversație)
- Limba: română, peste tot (conversație, UI, docs, mesajele de commit).
- Ritm: „continuă cu următorul pas” = un pas întreg din plan per mesaj; nu treci la pasul următor singur.
  Când are întrebări („ce trebuie să confirm…”), răspunde întâi, nu implementa.
- Deciziile de produs/sunet le ia el: înainte de pași cu alegeri vizibile, întreabă-l (AskUserQuestion,
  cu varianta recomandată prima). Deciziile tehnice le iei tu și le treci în `decisions.md`.
- Commit pe fiecare pas (`step NN: …`) **și push pe GitHub după fiecare pas** (cerut explicit).
- Vrea să fie anunțat cinstit despre greșeli și incidente, cu cauza și reparația.
- Nu șterge fișiere din `~/Music` (exporturile lui) fără să-l întrebi; datele de test create de tine le
  ștergi tu la final.
- Vrea, la final, ca serverul de dev să fie oprit când nu mai e folosit.

## 3. Unde am rămas (exact)
- Pașii 0–11 sunt implementați și pe GitHub. Ultimele commituri: `42175c3` (fix migrări), `03e5bfd` (README).
- **Deschis — criteriul pasului 8c:** utilizatorul trebuie să asculte cele 8 tranziții din mixul
  „Test beatmatch — ascultă tranzițiile” și să spună pentru fiecare: pe beat / ușor decalat (flam) /
  pe contratimp / derivă, eventual ce valoare din „Potrivirea beat-urilor” (−½, −10, +10, +½) a reparat-o.
  Criteriul: majoritatea pe beat fără corecție. Încă nu a răspuns.
  - Fișierul de ascultat era pe Mac: `~/Music/mixmatch/Test beatmatch — ascultă tranzițiile/…mp3`
    (57,8 min; tranzițiile la 9:49, 17:03, 21:57, 27:55, 34:10, 40:37, 46:18, 50:41). Pe alt calculator
    nu există decât dacă e copiat.
  - Mixul de test (9 piese, toate din `~/Music/House 🏠 Set 1` și `~/Music/tech house gramada`):
    Please, Stay → Blind (Frankie Knuckles Remix) → Revolution (Deep In Jersey Extended Mix) →
    Circus (Cagedbaby Mix) → How We Do → Restless (feat. Alex Mills) → Sing To Me Nina (Original Mix) →
    The Day (feat. Michelle Weeks) (Alaia & Gallo Remix) (Mixed) → If I Can't Get Down (Mousse T.'s Funky Shizzle Extended Mix).
    Toate tranzițiile Lin, 123–124 BPM.
  - Dacă răspunsul arată probleme: pe 80 de piese, față de Traktor, grila e pe beat la ~35–40, pe contratimp
    la ~13 (decizia de ½ beat greșește când basul de pe contratimp e mai tare decât kick-ul în 40–100 Hz).
    Următoarea îmbunătățire propusă: detecție de kick după atac (nu după nivel). Unealta:
    `backend/tools/evaluate_beatgrid.py 80` (are nevoie de colecția Traktor).
- **Opțional, cerut ca idee de utilizator, neconfirmat:** „Ascultă mixul” (redarea întregului mix în browser,
  cu planurile tranzițiilor, cursor pe cardurile mixului). Nu e în plan; întreabă înainte.
- Mărunțișuri notate: artiști dublați în tag-uri („Alex Mills, Alex Mills”); „Ce urmează după …” poate
  arăta versiuni diferite ale aceleiași piese (fișiere diferite, deci deduplicarea după conținut nu le prinde).

## 4. Ce s-a întâmplat și ce am învățat (nu e în altă parte, sau e împrăștiat)
- **Incidentul 0008 (2026-11-21):** migrarea a recreat `tracks` (batch SQLite) cu `PRAGMA foreign_keys = ON`
  → ștergere în cascadă: formele de undă, grilele, piesele din mixuri, setările tranzițiilor. Reparat:
  `alembic/env.py` rulează fără chei externe active + `PRAGMA foreign_key_check`; test de regresie în
  `tests/test_migrations.py`; analiza reface singură formele de undă/grilele lipsă. Conținutul mixului
  „Mix nou” al utilizatorului s-a pierdut definitiv (i s-a spus).
- **Beatmatch:** măsurătoarea automată între *perechi* de piese diferite e nesigură (vârfuri de corelație
  slabe); doar măsurătoarea *per piesă* față de Traktor e de încredere. Analiza, bucățile de previzualizare
  și exportul decodează **toate cu ffmpeg** (decodorul Essentia păstra amorsarea AAC, ~40 ms decalaj).
- **Verificări care au prins bug-uri reale** — păstrează obiceiul:
  - Chrome headless condus prin DevTools Protocol (script Node: `--remote-debugging-port`, `Runtime.evaluate`,
    `Input.dispatchMouseEvent/KeyEvent/DragEvent`, `Page.captureScreenshot`; `Fetch.enable` ca să interceptezi
    cereri și să nu scrii date de test în biblioteca utilizatorului). Scripturile erau în scratchpad și s-au
    pierdut; se refac ușor.
  - Randare offline în Chrome (`OfflineAudioContext` + `import('/src/audio/transition.ts')` din serverul Vite)
    comparată cu exportul: corelație ≥ 0,99, decalaj ≤ 0,02 ms.
  - Datele de test create în aplicația reală (mixuri, colecții) se șterg la final.
- **Capcane de unelte:**
  - `cmd | grep …` sau `| head` cu `set -o pipefail` ascund sau inventează eșecuri: verifică **codul de ieșire**
    al `make test` (Vitest iese cu eroare la „unhandled errors” chiar când scrie „N passed”).
  - `ruff format` / `prettier` reformatează cod între editări → înlocuirile de text exact pot să nu se mai
    potrivească; recitește fișierul înainte de editări mari.
  - `ruff --fix` scoate importuri încă nefolosite în momentul rulării.
  - Testele API au un fixture comun `client` (`tests/conftest.py`) care așteaptă joburile în curs și golește
    baza înainte și după — joburile de analiză rămase de la alt test suprascriau date.
  - Rotunjiri în virgulă mobilă: un început de bucată −0,000 a fost refuzat de server (`clipRanges` face max cu 0).

## 5. Specificul Mac-ului vechi (nu se mută)
- Muzica: `~/Music` (~550 MP3, ~600 M4A, ~180 FLAC, ~18 000 WAV, majoritatea sample-uri). În bibliotecă erau
  doar două foldere: `~/Music/House 🏠 Set 1` (38 MP3) și `~/Music/tech house gramada` (208 M4A) → 246 de piese.
- Colecția Traktor (referința pentru `backend/tools/`): `~/Documents/Native Instruments/Traktor 4.0.2/collection.nml`
  — ~2 900 de intrări, ~2 000 cu fișiere existente; `TEMPO BPM`, `MUSICAL_KEY VALUE` 0–23 (0–11 major,
  12–23 minor, ca clasă de înălțime), `CUE_V2 TYPE="4"` = AutoGrid (`START` în ms); cale = `DIR` (cu „/:” → „/”) + `FILE`.
  `test-tracks/reference.csv` (în .gitignore) avea 20 de piese alese din ea.
- ffmpeg acolo: 7.0.1, fără filtrul rubberband (nefolosit oricum: sincronizarea e stil vinil).
- `data/mixmatch.db` (local, neversionat): bibliotecă analizată (versiunea 5), mixul de test refăcut, „Mix nou” gol,
  un export. Se poate copia pe alt calculator doar dacă muzica e la aceleași căi.
