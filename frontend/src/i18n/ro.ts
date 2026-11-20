// Tot textul interfeței, în română.

export const ro = {
  appName: 'mixmatch',
  common: {
    close: 'Închide',
    cancel: 'Anulează',
  },
  errors: {
    network: 'Nu pot ajunge la server. Verifică dacă rulează `make dev`.',
    unexpected: 'Ceva n-a mers. Încearcă din nou.',
  },
  nav: {
    label: 'Secțiuni',
    library: 'Bibliotecă',
    mixes: 'Mix-uri',
    exports: 'Exporturi',
  },
  health: {
    checking: 'Se verifică serverul…',
    ok: 'Server conectat',
    down: 'Serverul nu răspunde',
  },
  library: {
    title: 'Biblioteca ta',
    subtitle: 'Tempo, tonalitate și energie detectate automat la import.',
    importButton: 'Importă piese',
    addFolderZone: 'Adaugă un folder cu muzică: MP3, FLAC, WAV, AIFF, M4A',
    trackCount: (n: number) => (n === 1 ? '1 piesă' : `${n} piese`),
    loading: 'Se încarcă biblioteca…',
    empty: 'Încă nu ai piese. Adaugă un folder și le găsim noi.',
    columns: {
      track: 'Piesă',
      duration: 'Durată',
    },
    unknownArtist: 'Artist necunoscut',
  },
  addFolder: {
    title: 'Adaugă un folder',
    intro: 'Scrie calea către un folder de pe calculator. Piesele rămân unde sunt; doar le citim.',
    pathLabel: 'Calea folderului',
    pathPlaceholder: '/Users/tu/Music/House',
    hint: 'În Finder: click dreapta pe folder, ține apăsat Option și alege „Copiază … ca nume de cale”.',
    submit: 'Scanează',
    scanning: 'Se scanează…',
    progressLabel: 'Progresul scanării',
    done: (n: number) => `Gata! Biblioteca are acum ${n === 1 ? '1 piesă' : `${n} piese`}.`,
    failed: 'Scanarea a eșuat:',
    shortSkipped: 'Fișierele mai scurte de un minut (sample-uri) nu intră în bibliotecă.',
  },
  screens: {
    mixes: {
      title: 'Mix-uri',
      subtitle: 'Aici vei construi și ordona seturile tale.',
    },
    exports: {
      title: 'Exporturi',
      subtitle: 'Aici vor apărea mixurile exportate, gata de descărcat.',
    },
  },
} as const;
