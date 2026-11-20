# Pasul 07 — Raportul mixului

## Ce am găsit înainte
`music/compat.py` (eticheta, scorul, motivul unei perechi), `api/mixes.py` (CRUD, ordinea),
Constructorul cu carduri sortabile, `/matches` pentru „Merg bine după ea”. `Mix.energy_shape`
exista în bază (implicit `free`), fără UI.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/music/compat.py` | schimbat | `problem` (cauza), `tempo_diff_pct`, `suggestion_rank` | raportul, `/matches` |
| `backend/mixmatch/music/energy_curve.py` | nou | `EnergyShape`, curbele dorite, ținta pentru piesa următoare | raportul; ordonarea (9) |
| `backend/mixmatch/mixes/report.py` | nou | raportul: tranziții, energie, avertismente (folosește `compat`, nu îl copiază) | `api/mixes.py` |
| `backend/mixmatch/api/mixes.py`, `db/models.py` | schimbat | `GET /mixes/{id}/report`; `PATCH` cu `energy_shape` | Constructorul |
| `backend/mixmatch/api/tracks.py` | schimbat | `/matches?exclude_mix=&target_energy=` | „Ce urmează după …” |
| `backend/tests/test_report.py`, `test_compat.py`, `test_api_mixes.py` | nou/schimbat | curbe, raport, cauze, sugestii după curbă | `make test` |
| `frontend/src/api/mixes.ts`, `api/tracks.ts` | schimbat | `useMixReport`, `useSetEnergyShape`, opțiuni pentru `useMatches` | Constructorul |
| `frontend/src/ui/Segmented.tsx` | nou | grupul de butoane din design | forma setului; lungimea tranziției (8a) |
| `frontend/src/features/mix-builder/{EnergyCurve,TransitionLink,NextSuggestions}.tsx` | noi | graficul, eticheta dintre carduri, sugestiile + legenda | Constructorul |
| `frontend/src/features/mix-builder/{MixBuilderScreen,MixTrackCard}.tsx` | schimbat | cardul curbei, etichetele, avertismentele, panoul din dreapta; coperta lată ca în machetă | — |
| `frontend/src/theme/GlobalStyle.tsx`, `features/library/LibraryScreen.tsx` | schimbat | `color-scheme: dark`; `minWidth: 0` (fără depășire pe orizontală) | — |

## Ce s-a făcut
- Între carduri: Lin / Bun / Atenție (formă + culoare + text), cu motivul la hover și pentru cititoarele de ecran.
- „Curba de energie”: segmented Încălzire / Urcare / Val / Liber; linia dorită punctată, mixul cu linie
  plină; punctul în care se intră printr-o tranziție „Atenție” e portocaliu.
- Bannerele de avertisment explică problema (ton, tempo sau energie) și ce poți face.
- Panoul „Ce urmează după …”: sugestii fără piesele din mix, ordonate și după curbă; „+” adaugă la final. Legenda.
- Schimbi ordinea → serverul recalculează raportul → etichetele, curba și avertismentele se actualizează.

## Verificat în aplicația reală
- Un mix de 6 piese construit din biblioteca ta (lanț de sugestii + o piesă de 156 BPM): Lin, Lin, Lin, Atenție, Bun.
- Găsit și reparat: trecerea 122 → 156 BPM era explicată ca „tonalitățile se ciocnesc”; cauza reală e tempo-ul
  (tonul se strică din cauza accelerării). Acum avertismentul spune „tempo-ul e prea departe (21,8 %)”.
- Chrome: „Urcare” → linia punctată apare; mutarea de la tastatură a lui „444” la final → avertismentul se mută
  pe noua pereche („Paradise Garage” → „First Breath”, 18,7 %).
- Găsit și reparat: panoul din dreapta ieșea din ecran (lipsea `minWidth: 0`); bara de derulare era albă.
- Mixul de test a fost șters la final.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (curbele, `EnergyShape` în `music/`, cauza „Atenție”,
  raportul, sugestiile după curbă, `PATCH`, etichetele în timpul drag-ului, „Rezolvă” în 8a, `color-scheme`).

## Cum testezi
- `make lint && make test && make types` (219 teste backend, 38 frontend).
- `make dev` → un mix cu câteva piese → schimbă forma, mută cardurile, adaugă din „Ce urmează după …”.

## Ce rămâne / atenție pentru pasul următor
- Pasul 8a: tabelul `transitions` (legat de pereche), `music/transition_plan.py` (lungime aliniată la fraze,
  stilurile, viteza lui B și auto-gain-ul în plan), ecranul Tranziție; eticheta dintre carduri devine link;
  butonul „Rezolvă” din banner deschide tranziția cu problema.
