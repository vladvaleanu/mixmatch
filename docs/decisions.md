# Jurnalul de decizii

Fiecare decizie de arhitectură sau de convenție se trece aici înainte de cod, cu data și motivul.
Cele mai noi sunt sus.

| Data | Decizie | Motiv |
| --- | --- | --- |
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
