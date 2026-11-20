// Tot textul interfeței, în română.

export const ro = {
  appName: 'mixmatch',
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
  screens: {
    library: {
      title: 'Biblioteca ta',
      subtitle: 'Aici vor apărea piesele tale, cu tempo, ton și energie detectate automat.',
    },
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
