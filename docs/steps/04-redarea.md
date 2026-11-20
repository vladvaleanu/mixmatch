# Pasul 04 — Redarea

## Ce am găsit înainte
`api/tracks.py` avea lista și `PATCH`; datele formei de undă erau deja în `waveforms` (1000 / 8000
de puncte), fără endpoint (mutat în acest pas în 3b). `ui/Waveform` desena doar bare fixe;
`features/library/` avea tabelul, dialogul și bannerul de analiză. Nu exista nimic în `audio/`.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/config.py` | schimbat | `cache_dir`; `analysis_version = 3` | `library/playback.py`, analiza |
| `backend/mixmatch/library/playback.py` | nou | fișierul de servit + media type; AIFF → FLAC în cache | `api/tracks.py` |
| `backend/mixmatch/api/tracks.py` | schimbat | `GET /tracks/{id}/audio` (Range), `GET /tracks/{id}/waveform?res=lo\|hi` | playerul, panoul |
| `backend/mixmatch/analysis/waveform.py` | schimbat | RMS în loc de vârf | analiza |
| `backend/tests/test_api_playback.py` | nou | Range, media types, AIFF, 404, rezoluții | `make test` |
| `frontend/src/audio/engine.ts` (+ test) | nou | singurul player: `toggle`, `playFrom`, `pause`, store `usePlayer` | butoanele de play, panoul |
| `frontend/src/api/tracks.ts` | schimbat | `trackAudioUrl`, `useWaveform` | panoul, butoanele de play |
| `frontend/src/ui/Waveform.tsx` | schimbat | grupare în N bare, progres, derulare (click/săgeți) | tabelul, panoul |
| `frontend/src/ui/PlayButton.tsx`, `EnergyDots.tsx` | nou/schimbat | butonul rotund; click-ul nu mai selectează rândul | tabelul, panoul |
| `frontend/src/features/library/{selectionStore,TrackPlayButton,TrackPanel}.ts(x)` | noi | selecția, play legat de player, panoul „Selectată” | `LibraryScreen`, `TrackTable` |
| `frontend/src/features/library/{LibraryScreen,TrackTable}.tsx`, `App.tsx`, celelalte ecrane | schimbat | coloana de play, rândul selectat, layout cu panou în dreapta; padding-ul trece în ecrane | — |

## Ce s-a făcut
- Play/pauză pe fiecare rând și în panou; un singur player în toată aplicația.
- Panoul „Selectată”: titlu, artist, forma de undă mare (progresul în accent, click = derulare),
  timpul, grila Tempo / Tonalitate / Energie (editabilă) / Intro-Outro.
- Forma de undă trece pe RMS: se văd structura și breakdown-urile (reanaliză automată, ~4 min).

## Verificat în aplicația reală (Chrome, condus prin DevTools)
- Selecție → play → după 3 s timpul arată 0:03; click la jumătatea formei de undă → 1:42 din 3:22.
- Play pe altă piesă din tabel → prima se oprește; un singur buton rămâne în „Pauză”.
- `GET /tracks/{id}/audio` cu `Range: bytes=1000-1999` prin proxy-ul Vite → 206, `audio/mp4`.
- Conversia AIFF e acoperită doar de testul automat: în `~/Music`, AIFF-urile sunt sample-uri.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (un singur `<audio>` + AudioContext, AIFF → FLAC
  în cache, forma de undă RMS, gruparea în panou, `camelCase` pentru starea locală).

## Cum testezi
- `make lint && make test && make types` (116 teste backend, 18 frontend).
- `make dev` → click pe titlul unei piese → panoul; play; click pe forma de undă mare.

## Ce rămâne / atenție pentru pasul următor
- Pasul 5: „Merg bine după ea” în panou (sub grilă), filtrele din bara laterală și căutarea din
  bara de sus. Bara laterală din machetă nu există încă; layout-ul are deja coloana centrală flexibilă.
- Butonul „Adaugă în mix” din panou vine în pasul 6.
- Playerul nu are încă auto-gain; câștigul vine din planul tranziției (pasul 8).
