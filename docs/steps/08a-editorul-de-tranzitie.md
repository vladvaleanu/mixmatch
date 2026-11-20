# Pasul 08a — Editorul de tranziție: planul și ecranul

## Ce am găsit înainte
`music/compat.py` (eticheta, cauza, viteza stil vinil), `mixes/report.py` (etichetele dintre carduri),
analiza cu `first_beat_s`, `intro_bars`, `outro_bars`, `loudness_lufs`, forma de undă `hi` (8000 de
puncte). Decizii de dinainte: tranziția legată de pereche, auto-gain spre −12 LUFS, sincronizare stil
vinil, implicit 16 bare + schimb de bas, „Alege pentru mine” după etichetă.

## Plan
| Fișier | Nou / schimbat | De ce | Cine îl folosește |
| --- | --- | --- | --- |
| `backend/mixmatch/music/compat.py` | schimbat | etichetele pe componente, `sync_speed` | planul, ecranul (chip-uri) |
| `backend/mixmatch/music/transition_plan.py` | nou | planul de automatizări (singura sursă) | API; browserul (8b), ffmpeg (10a) |
| `backend/mixmatch/db/models.py` + migrarea `0004` | schimbat/nou | tabelul `transitions` | API |
| `backend/mixmatch/api/transitions.py`, `api/mixes.py`, `main.py` | nou/schimbat | `GET …/plan`, `PATCH …/transitions/{pos}`; `load_mix` public; `ReportTransitionOut` | ecranul |
| `backend/tests/test_transition_plan.py`, `test_api_transitions.py` | noi | stiluri, fraze, lungimi, auto-gain, setări pe pereche, erori | `make test` |
| `frontend/package.json` | schimbat | `--default-non-nullable false` la `make types` | tipurile |
| `frontend/src/api/transitions.ts` | nou | `useTransition`, `useUpdateTransition` | ecranul |
| `frontend/src/features/transition/{TransitionScreen,TransitionView}.tsx` (+ test) | noi | ecranul și desenul (forme de undă, suprapunere, automatizări) | `App.tsx` |
| `frontend/src/features/mix-builder/{TransitionLink,MixBuilderScreen}.tsx` | schimbat | eticheta devine link; „Rezolvă” în avertismente | Constructorul |
| `frontend/src/theme/tokens.ts`, `i18n/ro.ts`, `App.tsx` | schimbat | `accentTint`, textele, ruta `/mixuri/:mixId/tranzitii/:position` | — |

## Ce s-a făcut
- Planul: viteza lui B, auto-gain pe fiecare deck, punctele de ieșire/intrare (lipite de fraze), lungimea
  (redusă dacă nu încape), automatizările de volum, bas și ecou pentru cele patru stiluri.
- Ecranul: titlul „A → B”, chip-urile (ton după sincronizare, tempo cu procentul lui B, energie), cele două
  forme de undă suprapuse în timpul real al mixului, zona de suprapunere („16 bare · 31 s”), liniile de
  automatizare și legenda; lungimea 8/16/32/64; stilurile ca radio cards; punctele (± o frază, automat);
  „Alege aplicația pentru mine”.
- În Constructor, eticheta dintre carduri și „Rezolvă” din banner deschid editorul.

## Verificat în aplicația reală
- Mix din biblioteca ta: „Body Funk (Extended Mix)” (122 BPM, outro 16) → „Veins” (124 BPM), Lin.
  Plan implicit: ieșirea la 6:50, 16 bare (31 s), B la −1,6 %, câștig −3,1 / −3,9 dB.
- Pe desen, tranziția implicită începe exact unde scade forma de undă a lui A (outro-ul detectat) și se
  termină la finalul piesei: prima confirmare reală a euristicii intro/outro din 3b.
- Chrome: „Ieșire cu ecou” + 32 de bare → „32 bare · 63 s”, B intră la mijloc, legenda arată „Ecou A”.
- Mixul de test a fost șters la final.

## Decizii
- Vezi primele intrări din `docs/decisions.md` (planul, stilurile, punctele implicite și lipirea de fraze,
  lungimea care încape, auto-gain și ecoul, tabelul, API-ul, schema, ecranul, `accentTint`).

## Cum testezi
- `make lint && make test && make types` (238 de teste backend, 41 frontend).
- `make dev` → un mix cu două piese analizate → click pe eticheta dintre carduri → schimbă lungimea,
  stilul, punctele; „Alege aplicația pentru mine”.

## Ce rămâne / atenție pentru pasul următor
- Pasul 8b: `audio/engine.ts` execută planul (două surse, GainNode, BiquadFilter low-shelf, DelayNode)
  doar pe fereastra tranziției; butonul „Ascultă tranziția”. Planul e complet: viteze, câștiguri, timpi.
- Grila de beat-uri (3a) nu e încă verificată la urechea: abia 8b o pune la încercare. La tempo mare
  (DnB) primul beat poate fi decalat.
