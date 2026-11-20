# Jurnalul de decizii

Fiecare decizie de arhitectură sau de convenție se trece aici înainte de cod, cu data și motivul.
Cele mai noi sunt sus.

| Data | Decizie | Motiv |
| --- | --- | --- |
| 2026-11-20 | Dependență pasul 3a: essentia (2.1b6.dev1389, wheel pentru Python 3.12 / arm64; aduce numpy). Licență AGPL, ok pentru uz personal | Analiza de tempo și ton, cum prevede planul |
| 2026-11-20 | Tempo: `RhythmExtractor2013(method="multifeature")`, valoarea Essentia rotunjită la o zecimală, fără rafinare din beat-uri | Pe 80 de piese: 69 exacte față de Traktor (eroare medie 0,05 BPM); rafinarea din beat-uri a stricat 24 de piese cu breakdown-uri |
| 2026-11-20 | Ton: `KeyExtractor(profileType="bgate")` | Pe 100 de piese comparate cu Traktor, `bgate` a avut cele mai puține tonuri greșite (16, față de 21 la `edma` și 23 la `edmm`) |
| 2026-11-20 | Analiza rulează ca job, în procese separate (`analysis_workers` = min(6, nuclee − 2)); pornește după fiecare scanare și la pornirea serverului, dacă există piese neanalizate | ~0,9 s pe piesă cu 4 procese; mixurile lungi ocupă câteva sute de MB fiecare, de aici limita de 6 |
| 2026-11-20 | O analiză eșuată primește și ea `analysis_version` (cu bpm/ton goale), ca să nu se reia la fiecare pornire; o piesă cu `file_hash` schimbat redevine neanalizată | Fără bucle infinite pe fișiere stricate; fișierele modificate se reanalizează |
| 2026-11-20 | Rezultatul analizei se salvează doar dacă rândul are tot aceeași cale | SQLite refolosește id-urile șterse; o rescanare în timpul analizei putea pune rezultatul pe altă piesă |
| 2026-11-20 | `GET /jobs/active` (joburile în lucru); `TrackOut` primește `bpm`, `key_camelot`, `key_name` (numele clasic, din `music/camelot.py`) și `analyzed` | Bannerul de analiză din Bibliotecă; frontendul nu calculează numele tonului |
| 2026-11-20 | BPM afișat fără zecimală când e întreg, altfel cu virgulă („123,5”) | Ca în machetă, cu formatul românesc |
| 2026-11-20 | Piesele de test: `backend/tools/evaluate_analysis.py pick` scrie `test-tracks/reference.csv` (20 de piese din `~/Music`, din colecția Traktor), `run` raportează acordul | Măsurarea se poate repeta la fiecare schimbare de algoritm |
| 2026-11-20 | Dependențe pasul 2: backend mutagen (metadate); frontend zustand (starea UI: dialog, toast) și openapi-fetch (client tipat din `schema.d.ts`) | Metadatele vin din plan; openapi-fetch evită tipurile scrise de mână pentru cereri |
| 2026-11-20 | `file_hash` = SHA-256 peste mărime + primii și ultimii 64 KB, nu peste tot fișierul | Rescanarea a sute de piese durează secunde; schimbarea fișierului tot se detectează |
| 2026-11-20 | Tag-urile WAV se citesc și din chunk-ul RIFF LIST/INFO (INAM, IART), nu doar din ID3 | Toate WAV-urile verificate din biblioteca utilizatorului au tag-urile doar în INFO |
| 2026-11-20 | Fără tag de titlu: titlul și artistul se deduc din numele fișierului („08. Artist - Titlu”) | Multe fișiere sunt numite așa |
| 2026-11-20 | Rescanarea șterge din `tracks` piesele ale căror fișiere au dispărut din folder; fișierele ascunse (`.`, `._`) și folderele `.`/`$` se ignoră | Biblioteca reflectă discul; fișierele AppleDouble și `$RECYCLE.BIN` nu sunt muzică |
| 2026-11-20 | O singură scanare odată: `POST /library/folders` întoarce 409 `scan_in_progress` dacă una rulează; același folder adăugat din nou = rescanare | Două scanări simultane ar concura pe aceleași rânduri |
| 2026-11-20 | Erorile API trec printr-un singur handler (`api/errors.py`), inclusiv validarea (422 `invalid_request`) și 404; în frontend, `unwrap` le transformă în `ApiError`, iar QueryClient le arată în toast-ul global (cererile `meta.silent` nu) | Forma `{"error": …}` peste tot și un singur loc de afișare |
| 2026-11-20 | Butonul principal din bara de sus („Importă piese”) duce în Bibliotecă și deschide dialogul „Adaugă folder”; zona punctată din Bibliotecă deschide același dialog până la drag & drop (pasul 11) | Browserul nu dă calea fișierelor; utilizatorul scrie sau lipește calea |
| 2026-11-20 | Tokens noi: `overlay` (fundalul dialogurilor) și `zIndex` (dialog, toast) | Necesare pentru dialog și toast; trecute și în design.md |
| 2026-11-20 | Dependențe backend pasul 1: sqlalchemy ≥ 2, alembic | Baza de date și migrările, ca în plan |
| 2026-11-20 | Baza stă în `data/mixmatch.db` (folderul se schimbă cu `MIXMATCH_DATA_DIR`); SQLite cu WAL și `foreign_keys = ON` | Un singur fișier local; WAL lasă citirile din API să meargă în timp ce joburile scriu |
| 2026-11-20 | Migrările rulează automat la pornirea backendului (lifespan), apoi joburile rămase `queued`/`running` devin `failed` cu motivul „întrerupt” | Aplicație locală: baza e mereu la zi; coada e în proces, deci un job neterminat nu mai poate continua după repornire |
| 2026-11-20 | Starea joburilor: `queued` → `running` → `done` / `failed`; tipuri: `scan`, `analysis`, `export`; `progress` între 0 și 1 | Stări simple, suficiente pentru bara de progres |
| 2026-11-20 | Constrângeri cu nume stabile (naming convention) și migrări în mod batch | SQLite nu suportă ALTER complet; batch-ul are nevoie de nume pentru constrângeri |
| 2026-11-20 | Un test compară modelele cu migrările (`compare_metadata`) | Un model schimbat fără migrare pică testele |
| 2026-11-20 | Sincronizarea tempo-ului în tranziții: stil vinil (viteza și tonul se schimbă împreună), fără time-stretch. Raportul `bpm_A / bpm_B` intră în planul tranziției; browserul folosește `playbackRate`, ffmpeg `asetrate` + `aresample` | Ales de utilizator; previzualizarea și exportul sună identic, fără biblioteci de time-stretch |
| 2026-11-20 | Setările unei tranziții sunt legate de perechea (from_track_id, to_track_id) din mix, nu de poziție | Ales de utilizator; o reordonare nu mută setări pe alte piese |
| 2026-11-20 | Exportul din MVP: doar WAV/MP3, tracklist și .cue; Rekordbox XML și Serato după MVP | Ales de utilizator |
| 2026-11-20 | Piesele de test pentru 3a: ~20 de piese din `~/Music`, cu BPM și ton din colecția Traktor 4 ca referință; în `test-tracks/` stă doar lista, nu copii ale fișierelor | Utilizatorul are ~2.000 de piese analizate în Traktor; acuratețea se măsoară ca acord cu Traktor |
| 2026-11-20 | Formatele suportate: MP3, FLAC, WAV, AIFF și M4A | Ales de utilizator; ~600 de piese din bibliotecă sunt M4A |
| 2026-11-20 | Scanarea ignoră fișierele sub 60 s (prag în `config.py`) | Ales de utilizator; `~/Music` are ~18.000 de sample-uri WAV |
| 2026-11-20 | Ecranul Mix-uri: lista mixurilor ca carduri (nume, piese, durată, dată) + „Mix nou”; click deschide Constructorul | Ales de utilizator; nu exista machetă |
| 2026-11-20 | Filtrul „Tonalitate” rămâne: `GET /tracks?key=8A&key=9A`, pe lângă `compatible_with` | Ales de utilizator; apare în macheta Biblioteca |
| 2026-11-20 | Tabel nou `exports` (mix_id, job_id, format, path, duration_s, created_at) și rutele `GET /exports`, `GET /exports/{id}/file` | Ecranul Exporturi are nevoie de istoric; `jobs` nu păstrează fișierul rezultat |
| 2026-11-20 | `GET /tracks` fără paginare în MVP | O bibliotecă de câteva mii de piese încape într-un răspuns; se revizuiește dacă tabelul devine lent |
| 2026-11-20 | Makefile-ul folosește explicit `python3.12` (sau 3.13), nu `python3`; venv-ul stă în `backend/.venv` | Pe mașina utilizatorului `python3` e 3.11 |
| 2026-11-20 | Dependențe backend pasul 0: fastapi, uvicorn[standard]; dev: pytest, httpx2 (cerut de TestClient-ul Starlette 1.x), ruff | Minimul pentru `/api/health` și unelte |
| 2026-11-20 | Dependențe frontend pasul 0: React 18.3, react-router-dom 7, TanStack Query 5, @fontsource/inter și @fontsource/space-grotesk; dev: Vite 8, TypeScript 5.9, eslint 10 + typescript-eslint + react-hooks, prettier, Vitest 5 + jsdom + Testing Library, openapi-typescript 7 | TypeScript rămâne pe 5.9: typescript-eslint și openapi-typescript nu suportă încă TS 7 |
| 2026-11-20 | Rutare cu react-router-dom; rutele sunt în română: `/biblioteca`, `/mixuri`, `/exporturi` | Editorul de tranziție va avea nevoie de rute cu parametri; refresh-ul păstrează ecranul |
| 2026-11-20 | Fonturile se servesc local prin @fontsource, nu de la Google Fonts | Aplicația e locală și trebuie să meargă fără internet |
| 2026-11-20 | Stilurile sunt inline, din `theme/tokens.ts`; stilurile globale (body, focus) sunt generate din tokens în `theme/GlobalStyle.tsx` | O singură sursă pentru culori și spațieri, fără fișiere CSS cu valori duplicate |
| 2026-11-20 | `accentSoftBg` din design.md se împarte în `accentSoftBg` (`#1F2418`) și `accentSoftBgStrong` (`#2C3320`) | design.md dădea două valori pentru același token |
| 2026-11-20 | `make types`: `python -m mixmatch.openapi` scrie `backend/openapi.json` (în .gitignore), apoi openapi-typescript scrie `frontend/src/api/schema.d.ts` (în git) | Schema se generează fără să pornească serverul; diferențele de API se văd în schema.d.ts |
| 2026-11-20 | Rutele includ prefixul `/api` în schema OpenAPI; `api/client.ts` primește calea completă (ex. `/api/health`) | Căile din tipuri coincid 1:1 cu cele din cereri |
| 2026-11-20 | Dezvoltarea continuă local, în VS Code, cu Claude Code | Utilizatorul lucrează direct pe mașina lui |
| 2026-11-20 | Numele proiectului: **mixmatch**; pachetul Python: `mixmatch` | Ales de utilizator |
| 2026-11-20 | Codul stă în repo-ul GitHub privat `vladvaleanu/mixmatch`, cu un commit pe pas | Fiecare sesiune nouă reia lucrul din repo și din notele de pas |
| 2026-11-20 | Un prompt = un pas; pașii 3, 8 și 10 sunt împărțiți în a/b | Pașii mari ies mai curat în două bucăți testabile |
| 2026-11-20 | Agentul face tot pasul fără confirmare intermediară; planul se scrie în nota pasului | Ales de utilizator |
| 2026-11-20 | Energia se calculează automat și se poate corecta de mână (`energy_manual` are prioritate) | Analiza automată va greși uneori |
| 2026-11-20 | Backend Python local + frontend React | Analiză mai precisă, depanare ușoară, poate rula mai târziu pe un server de acasă |
| 2026-11-20 | Logica muzicală doar în `backend/mixmatch/music/` | Un singur loc pentru reguli, fără diferențe între UI și export |
| 2026-11-20 | Tranziția ca plan de automatizări, executat și de browser, și de ffmpeg | Previzualizarea și exportul sună la fel |
| 2026-11-20 | Importul din MVP = folder pe disc; drag & drop în pasul 11 | Browserul nu dă calea fișierelor |
| 2026-11-20 | UI în română, cu textele în `i18n/ro.ts` | Limba utilizatorului; permite o engleză mai târziu |
