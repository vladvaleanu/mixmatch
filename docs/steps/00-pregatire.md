# Pregătire (înainte de pasul 0)

## Ce există
Doar documentația: `CLAUDE.md`, `docs/plan.md`, `docs/decisions.md`, `docs/design.md`,
machetele din `docs/design/mockups/` și acest folder `docs/steps/`. Încă nu există cod.

## Ce s-a decis
- Conceptul și cele trei ecrane (Biblioteca, Constructorul de mix, Editorul de tranziție) au fost
  făcute pe un canvas de design.
- Planul de implementare are 12 pași (0–11), iar pașii 3, 8 și 10 sunt împărțiți în a/b.
- Toate deciziile sunt în `docs/decisions.md`.

## Următorul pas
**Pasul 0 — Scheletul** (vezi `docs/plan.md`, secțiunea 5).

## Ce trebuie să existe pe mașina utilizatorului
Python ≥ 3.12, Node ≥ 20, ffmpeg, git. Pasul 0 adaugă `make setup`, care le verifică.
