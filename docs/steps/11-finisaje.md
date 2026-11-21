# Pasul 11 — Finisaje

## Ce am găsit înainte
Zona punctată din Bibliotecă deschidea doar „Adaugă folder” (cale scrisă de mână); bara laterală avea
doar filtrele; stările goale erau o propoziție; nu existau scurtături. Machetele aveau „Colecții”
(Toate piesele, Adăugate recent, colecțiile utilizatorului) și textul „Trage aici un folder sau fișiere…”.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/pyproject.toml`, `config.py` | schimbat | `python-multipart`; `uploads_dir` | upload |
| `backend/mixmatch/api/library.py` | schimbat | `start_scan` comun, `POST /library/upload` | Biblioteca |
| `backend/mixmatch/db/models.py` + migrarea `0008` | schimbat/nou | `tracks.added_at`, `collections`, `collection_tracks` | colecțiile |
| `backend/mixmatch/api/collections.py`, `api/tracks.py`, `main.py`, `text.py` | nou/schimbat | CRUD colecții, filtrul și sortarea `recent`, `collection_ids`, sortare fără diacritice | Biblioteca |
| `backend/tests/test_api_upload.py`, `test_api_collections.py`, `test_text.py`, `conftest.py` | noi/schimbat | upload, colecții, sortare | `make test` |
| `frontend/src/api/library.ts`, `api/collections.ts`, `api/tracks.ts` | schimbat/nou | `useUploadTracks`, colecțiile, filtrul `collection` | Biblioteca |
| `frontend/src/features/library/{dropFiles,UploadDialog,ScanProgress,CollectionsNav,CollectionToggles,useLibraryShortcuts}.ts(x)` | noi | drop recursiv, importul, progresul comun, colecțiile, scurtăturile | `LibraryScreen`, `Sidebar`, `TrackPanel` |
| `frontend/src/ui/{EmptyState,ShortcutsHelp,isTyping}.ts(x)` | noi | starea goală, lista scurtăturilor („?”, „/”), paza pentru câmpuri | ecranele, `App.tsx` |
| `frontend/src/features/library/{LibraryScreen,AddFolderDialog,Sidebar,TrackPanel,TrackTable,LibrarySearch,filterStore}`, `features/exports/ExportsScreen.tsx`, `App.tsx`, `i18n/ro.ts` | schimbat | legarea în ecrane | — |

## Ce s-a făcut și unde apare
- **Drag & drop cu upload** (Biblioteca, zona punctată): fișiere sau foldere întregi (parcurse recursiv),
  doar audio; copiate în `~/Music/mixmatch/Importate`, scanate și analizate; zona se aprinde la tragere;
  fereastra „Import” arată copierea, apoi scanarea. Apăsat, zona deschide în continuare „Adaugă folder”.
- **Colecții** (bara laterală + panoul piesei): Toate piesele, Adăugate recent, colecțiile tale cu numărul de
  piese, „+ Colecție nouă”, ștergere cu confirmare; în panou, comutatoare pentru fiecare colecție. Țin loc și
  de tag-uri. Sortarea „adăugate recent” e și în lista „Sortat după”.
- **Stări goale**: Biblioteca goală și Exporturi au un card cu explicație și o acțiune.
- **Scurtături** (oriunde în Bibliotecă; „?” în bara de sus): Spațiu, ↑ ↓ / K J, „/”, „?”, Esc.

## Verificat în aplicația reală (Chrome, condus prin DevTools)
- Drop real al unui fișier pe zonă (cu cererea de upload interceptată, ca să nu intre piese de test în
  biblioteca ta): zona arată „Lasă fișierele aici”, cererea conține `test.mp3`, fereastra trece la scanare.
- Colecție temporară creată din „+ Colecție nouă”, o piesă adăugată din panou, filtrul arată 1 piesă; ștearsă la final.
- Tastatură: ↓ ↓ selectează a doua piesă, Spațiu o pornește, „?” deschide lista.
- Găsit și reparat: corectura energiei întorcea piesa fără colecții (ar fi „dispărut” din colecții în listă);
  ordinea alfabetică punea „Încălzire” după „Vârf” (diacritice).

## Decizii
- Vezi primele intrări din `docs/decisions.md` (python-multipart, folderul administrat, upload într-o cerere,
  colecții ca tag-uri, `added_at`, colecția ca navigare, sortarea fără diacritice, scurtăturile, stările goale).

## Cum testezi
- `make lint && make test && make types` (402 teste backend, 67 frontend).
- `make dev` → trage un folder în Bibliotecă; creează o colecție; apasă „?”.

## Ce rămâne / atenție
- Planul (pașii 0–11) e complet. Rămân deschise: confirmarea prin ascultare a pasului 8c și ideea
  „Ascultă mixul” (redarea întregului mix în browser), dacă utilizatorul o vrea.

## Incident descoperit după pas (2026-11-21)
- Migrarea `0008` (coloana `tracks.added_at`) a recreat tabela `tracks` cu cheile externe active, iar
  SQLite a șters în cascadă: formele de undă, grilele de beat-uri, piesele din cele două mixuri și setările
  tranzițiilor. Piesele, analiza de bază, mixurile (ca nume), exporturile și fișierele au rămas.
- Reparat: migrările rulează fără chei externe active, cu verificare de integritate la final; test de regresie
  (date la 0007 → upgrade → rândurile rămân). Analiza reface singură formele de undă și grilele lipsă.
- Conținutul mixului de test se poate reface din tracklistul exportat; conținutul „Mix nou” s-a pierdut.
