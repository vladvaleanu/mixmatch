<!-- MIGRARE TEMPORARĂ -->
> **MIGRARE TEMPORARĂ — citește întâi `docs/HANDOFF.md` și urmează-i instrucțiunile.**
> Proiectul a fost mutat pe alt calculator; handoff-ul conține contextul conversației anterioare.
> După ce utilizatorul confirmă migrarea, șterge acest bloc (cu marcajele) și `docs/HANDOFF.md`
> (vezi „Pasul 4” din handoff).
<!-- /MIGRARE TEMPORARĂ -->

# mixmatch — reguli de lucru

Aplicație web locală pentru construit mixuri DJ din piesele proprii. Backend Python
(FastAPI, SQLite, Essentia), frontend React + TypeScript (Vite). Limba de lucru și a
UI-ului: română.

Documente de citit, în ordinea asta:
1. `docs/plan.md` — scopul, arhitectura, modelul de date, API-ul și pașii 0–11.
2. `docs/decisions.md` — deciziile luate. Ce scrie acolo nu se schimbă fără o decizie nouă.
3. `docs/design.md` — culorile, fonturile, componentele și ecranele (machetele sunt în `docs/design/mockups/`).
4. `docs/steps/` — câte o notă pentru fiecare pas terminat. Ultima notă îți arată unde am rămas.

## Cum lucrăm
- Utilizatorul spune „continuă cu pasul X” (sau 3a, 3b, 8a, 8b, 10a, 10b).
- Un prompt = un pas întreg: citești, planifici, implementezi, verifici, documentezi.
- Nu treci la pasul următor fără să ți se ceară.

## Înainte de orice cod
1. Citește `docs/decisions.md` și ultima notă din `docs/steps/`.
2. Citește secțiunea pasului din `docs/plan.md`, apoi fișierele din „Citește înainte”,
   plus fișierele care le importă sau pe care le importă ele.
3. Scrie în 3–5 rânduri ce există deja, ce convenții folosește codul și unde se leagă pasul.
4. Scrie planul de fișiere (ce se schimbă, ce apare, de ce, cine folosește fiecare fișier)
   în nota pasului, apoi implementează. Oprește-te și întreabă doar dacă planul
   contrazice `docs/plan.md` sau `docs/decisions.md`.

## Reguli
- Nu crea un fișier, o funcție sau o componentă nouă dacă una existentă poate fi extinsă.
- Nu scrie cod pe care nu îl folosește nimic în acest pas. Nimic „pentru mai târziu”.
- Logica muzicală (ton, tempo, scoruri, tranziții) stă doar în `backend/mixmatch/music/`.
  Frontendul afișează, nu recalculează.
- Tranziția e un plan de automatizări produs de `music/transition_plan.py`. Browserul
  (`frontend/src/audio/`) și ffmpeg (`export/`) execută același plan.
- Frontendul apelează API-ul doar prin `frontend/src/api/`. Tipurile vin din `make types`
  (openapi-typescript), nu se scriu de mână.
- Web Audio se atinge doar în `frontend/src/audio/`.
- Culorile și spațierile vin doar din `frontend/src/theme/tokens.ts` (valorile sunt în `docs/design.md`).
- Textul din UI stă în `frontend/src/i18n/ro.ts`.
- Unități: secunde (`_s`), bare (`_bars`), BPM cu o zecimală, ton în Camelot (`8A`).
  Numele clasic („La minor”) e doar afișare.
- Câmpurile API sunt `snake_case` și rămân așa până în frontend.
- Erorile API au forma `{"error": {"code": "...", "message": "..."}}`.
- Energia: `energy` (automată, 1–5) și `energy_manual` (1–5 sau null). Valoarea efectivă
  este `energy_manual ?? energy`, calculată într-un singur loc în backend.
- Nu adăuga dependențe fără să le treci în `docs/decisions.md`.

## După cod
- `make lint && make test && make types` — toate trebuie să treacă, iar `make dev` trebuie să pornească.
- Scrie `docs/steps/NN-nume.md` după șablonul din `docs/steps/README.md`.
- Commit cu mesajul `step NN: <ce>`.
- Dacă nu ești sigur de ceva, întreabă. Nu ghici structura codului.
