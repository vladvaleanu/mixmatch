# mixmatch — design

Interfață întunecată, aerisită, cu o singură culoare de accent. Prietenoasă, minimală,
ușor de folosit. Valorile de mai jos se mută 1:1 în `frontend/src/theme/tokens.ts`.

Canvasul cu machetele, editabil: https://claude.ai/artifact/QVeK1q9AuiuF8ddLfzo2T3
Sursa machetelor: `docs/design/mockups/` (vezi README-ul de acolo).

## Tokens

### Culori
| Token | Valoare | Folosire |
| --- | --- | --- |
| `bg` | `#111214` | fundalul aplicației |
| `surface` | `#16171A` | carduri mari, tabel |
| `surface2` | `#1A1B1F` | carduri mici, câmpuri, butoane secundare |
| `surface3` | `#22242A` | rând selectat, tab activ |
| `control` | `#24262C` | butoane rotunde (play, +) |
| `border` | `#24252B` | separatoare, contururi |
| `borderStrong` | `#2A2C33` | contururi de câmpuri și butoane |
| `borderDashed` | `#34363E` | zona de drop, „Adaugă”, puncte inactive |
| `text` | `#F2F2F0` | text principal |
| `textSoft` | `#C9CAD0` | text secundar pe suprafețe |
| `textMuted` | `#A4A6AE` | etichete, meta (contrast ≥ 4.5:1 pe `bg`) |
| `waveIdle` | `#6B6E78` | forma de undă a pieselor neselectate |
| `accent` | `#C6F36B` | butonul principal, selecție, „Lin”, energie plină |
| `accentText` | `#111214` | text pe accent |
| `accentSoftBg` | `#1F2418` | fundal pentru chip-uri „Lin” |
| `accentSoftBgStrong` | `#2C3320` | fundal pentru filtru activ |
| `accentSoftText` | `#E2FFA8` | text pe accentSoftBg |
| `info` | `#7FB2FF` | „Bun”, linia schimbului de bas |
| `infoSoftBg` / `infoSoftText` | `#1A2130` / `#CFE0FF` | chip „Bun” |
| `warn` | `#F5B85B` | „Atenție” |
| `warnSoftBg` / `warnSoftText` | `#2A2418` / `#FFE2A8` | banner și chip „Atenție” |

Etichetele tranzițiilor nu se bazează doar pe culoare. Fiecare are și o formă proprie:
cerc pentru Lin, pătrat pentru Bun, romb pentru Atenție.

Culoarea tonului (KeyPill): `hsl((n*30 + 60) % 360, 60%, 74%)`, cu text `#111214`, unde n e
cifra Camelot. Coperta-placeholder a unei piese: aceeași nuanță, `hsl(…, 35%, 32%)`.

### Tipografie
- Text: **Inter** 400/500/600, de bază 14px; meta 13px; etichete 12px (majuscule, letter-spacing 0.06em).
- Titluri: **Space Grotesk** 600: H1 32px (letter-spacing −0.02em), logo 20px, titlu de panou 24px.
- Cifre: `font-variant-numeric: tabular-nums` pentru BPM și durate.

### Spațiere și forme
- Pași de spațiere: 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32.
- Raze: 8 (pastile mici), 10 (butoane mici), 12 (câmpuri, butoane, carduri mici), 14 (carduri mari, tabel), 16 (secțiuni), 999 (pastile rotunde).
- Ținte de atingere ≥ 40–44px. Butonul principal are 44–48px înălțime.
- Fără umbre, fără gradiente, fără emoji. Iconițe: SVG inline cu contur de 2px.

## Componente (în `frontend/src/ui/`)
- **TopBar**: logo (cerc cu punct, în accent) + „mixmatch”, nav pastile (Bibliotecă, Mix-uri, Exporturi), căutare, buton principal.
- **Button**: primary (accent), secondary (surface2 + borderStrong), icon (rotund, control).
- **Chip / Pill**: meta, filtre, etichete de stare.
- **KeyPill**: codul Camelot pe culoarea tonului.
- **EnergyDots**: 5 puncte de 8px; cele pline în accent, restul în `borderDashed`.
- **Waveform**: bare de 2px cu spațiu de 2px; înălțimea vine din vârfuri; culoarea e `waveIdle` sau `accent` (selectat).
- **TransitionTag**: Lin / Bun / Atenție, cu formă și culoare.
- **Segmented**: grup de butoane cu `aria-pressed` (forma setului, lungimea tranziției).

## Ecrane

### 1. Biblioteca (`features/library/`)
Trei coloane care se așază una sub alta pe ecrane înguste:
- **Bara laterală (220–260px)**: Colecții; Filtre (tempo min/max, energie 1–5, „doar compatibile cu …”); nota „Totul se analizează local”.
- **Centru**: H1 „Biblioteca ta” + subtitlu; zona de drop (chenar punctat); tabelul: play, piesă (copertă, titlu, artist), BPM, Ton, Energie, Durată, Formă de undă. Rândul selectat are fundalul `surface3`.
- **Panoul din dreapta (300–380px)**: „Selectată”, titlu și artist, forma de undă mare, grila 2×2 (Tempo, Tonalitate, Energie, Intro/Outro), butonul „Adaugă în mix”, lista „Merg bine după ea” (copertă, titlu, motiv, chip Lin/Bun).

### 2. Constructorul de mix (`features/mix-builder/`)
- Antet: numele mixului, meta („7 piese · 43 min · 120 → 128 BPM”), butoanele „Ordonează automat” (secundar) și „Ascultă mixul” (principal).
- Cardul „Curba de energie”: segmented Încălzire / Urcare / Val / Liber; graficul cu forma dorită (punctată, gri) și mixul (linie plină în accent, câte un punct pe piesă; punctul unei tranziții cu probleme e în `warn`).
- „Ordinea pieselor”: rând orizontal de carduri (168px: număr, mâner de drag, copertă, titlu, artist, BPM · KeyPill · E). Între carduri stă un TransitionTag pe care dai click și deschide editorul de tranziție. La final, cardul „Adaugă”.
- Bannerul de avertisment (warnSoftBg) explică problema și are butonul „Rezolvă”.
- Panoul din dreapta: „Ce urmează după <ultima piesă>?”, cu sugestii și buton +, plus legenda tranzițiilor.

### 3. Editorul de tranziție (`features/transition/`)
- „Înapoi la <mix>”; titlul „A → B”; chip-uri pentru ton, tempo și energie.
- Cardul cu cele două forme de undă: A (gri) pe ~80% din lățime, B (accent) de la ~55%. Zona de suprapunere e marcată în accent (cu durata în bare și secunde). Dedesubt: liniile de automatizare (volum A, volum B, schimbul de bas punctat) și legenda.
- Lungimea: segmented 8 / 16 / 32 / 64 bare, plus nota despre alinierea la fraze.
- Stilul: radio cards (Schimb de bas, Crossfade simplu, Ieșire cu ecou, Tăietură pe beat), fiecare cu o explicație scurtă.
- Butoanele „Ascultă tranziția” (principal) și „Alege aplicația pentru mine”.

### 4. Mix-uri (`features/mix-builder/`)
Nu are machetă. H1 „Mix-urile tale”, butonul principal „Mix nou”, apoi o grilă de carduri
(`surface`, rază 14): numele mixului, „7 piese · 43 min”, data ultimei modificări. Click pe card
deschide Constructorul. Stare goală: un card punctat (`borderDashed`) „Creează primul mix”.

### 5. Exporturi (`features/exports/`)
Nu are machetă. Se face în stilul celorlalte: listă de exporturi, progres, descărcare.

## Textul interfeței
În română, cu ton prietenos și direct („Trage aici un folder…”, „Merg bine după ea”).
Totul stă în `i18n/ro.ts`.
