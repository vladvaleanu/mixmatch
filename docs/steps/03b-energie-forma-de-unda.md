# Pasul 03b — Analiza: energie, formă de undă, intro/outro

## Ce am găsit înainte
Analiza din 3a: `analysis/track.py` (`analyze_file`, rulează în procese separate) cheamă
`tempo.py` și `key.py`; `runner.py` salvează rezultatul și reia piesele cu `analysis_version` vechi.
`Track` avea deja `energy`, `energy_manual`, `intro_bars`, `outro_bars`. Tabelul din Bibliotecă
avea Piesă, BPM, Ton, Durată. Deciziile luate înainte de pas: energie din praguri fixe, auto-gain
(deci tăria în LUFS), corectura energiei direct din tabel.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/analysis/audio.py` | schimbat | o singură citire: stereo (rata originală) + mono 44,1 kHz | `track.py` |
| `backend/mixmatch/analysis/loudness.py` | nou | tăria integrată EBU R128 | `track.py`; auto-gain (pasul 8a) |
| `backend/mixmatch/analysis/energy.py` | nou | caracteristici, scor, praguri calibrate | `track.py` |
| `backend/mixmatch/analysis/structure.py` | nou | intro/outro în bare | `track.py` |
| `backend/mixmatch/analysis/waveform.py` | nou | vârfuri 40 / 1000 / 8000 | `track.py`, `runner.py` |
| `backend/mixmatch/analysis/track.py`, `runner.py` | schimbat | rezultatul complet; salvează și forma de undă | jobul de analiză |
| `backend/mixmatch/db/models.py` + migrarea `0002` | schimbat/nou | `tracks.loudness_lufs`, tabelul `waveforms`, `Track.energy_effective` | analiza, API |
| `backend/mixmatch/config.py` | schimbat | `analysis_version = 2` | `runner.py` |
| `backend/mixmatch/api/tracks.py` | schimbat | `energy`, `energy_manual`, intro/outro, `waveform_preview`; `PATCH /tracks/{id}` | tabelul |
| `backend/tests/test_analysis_parts.py` + teste extinse | nou/schimbat | energie, structură, vârfuri, PATCH, cascada | `make test` |
| `frontend/src/ui/EnergyDots.tsx`, `Waveform.tsx` | noi | punctele de energie (cu corectare), forma de undă | tabelul; panoul (pasul 4) |
| `frontend/src/api/tracks.ts` | schimbat | `useSetEnergy` | tabelul |
| `frontend/src/features/library/TrackTable.tsx`, `i18n/ro.ts` | schimbat | coloanele Energie și Formă de undă | Biblioteca |

## Ce s-a făcut
- Analiza calculează acum și energia (1–5), tăria (LUFS), intro/outro (bare) și forma de undă.
- Tabelul arată ca macheta Biblioteca: copertă, piesă, BPM, ton, energie, durată, formă de undă.
- Energia se corectează cu click pe puncte; click pe valoarea manuală curentă revine la automat.
  Valoarea efectivă (`energy_manual ?? energy`) se calculează doar în backend.

## Calibrarea energiei
200 de piese aleatorii din `~/Music`. Medii pe folder (energia 1–5): minimal house 1,5,
groove hop 1,6, tech house 2,8–3,1, hard20-4 3,7, HARDGROOVE 4,4, hardgroove2 4,5, hg3 4,8.
Constantele sunt în `analysis/energy.py`. Pe cele 246 de piese din bibliotecă (house și tech house):
1 → 42, 2 → 74, 3 → 74, 4 → 45, 5 → 11.

## Verificat pe biblioteca reală
- La pornire, versiunea 2 a reanalizat singură cele 246 de piese, în ~4 min: toate au energie
  și formă de undă.
- Intro: 0 bare la 124 de piese (multe sunt radio edit-uri care încep direct cu tot beat-ul), 8 sau 16 bare la 81.
  Outro: 0–8 bare la cele mai multe.
- `PATCH /tracks/{id}`: 1 → efectivă 1; null → înapoi la automat (4); 7 → 422 `invalid_request`.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (scorul de energie, EBU R128, euristica intro/outro,
  cele trei rezoluții, mutarea `GET /tracks/{id}/waveform` în pasul 4, `energy_effective`).

## Cum testezi
- `make lint && make test && make types` (107 teste backend, 14 frontend).
- `make dev` → Biblioteca: click pe al cincilea punct al unei piese → 5 (corectată);
  click din nou pe el → revine la valoarea automată.

## Ce rămâne / atenție pentru pasul următor
- Pasul 4: `GET /tracks/{id}/waveform?res=lo|hi` (datele sunt deja în `waveforms`), redarea,
  panoul „Selectată” cu grila Tempo / Tonalitate / Energie / Intro-Outro și `EnergyDots` editabil.
- Forma de undă folosește vârful pe fiecare interval; la masterele foarte tari arată aproape plin.
  Dacă în panoul mare nu se văd breakdown-urile, se poate trece la RMS (cere `analysis_version` 3).
- Intro/outro e o euristică după tăria pe bare; pasul 8a o va verifica pe tranziții reale.
