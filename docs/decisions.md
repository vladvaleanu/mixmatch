# Jurnalul de decizii

Fiecare decizie de arhitectură sau de convenție se trece aici înainte de cod, cu data și motivul.
Cele mai noi sunt sus.

| Data | Decizie | Motiv |
| --- | --- | --- |
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
