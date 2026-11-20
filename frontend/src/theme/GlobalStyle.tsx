import { color, font, fontSize } from './tokens';

// Stilurile de bază ale documentului, construite din tokens.
const css = `
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  background: ${color.bg};
  color: ${color.text};
  font-family: ${font.text};
  font-size: ${fontSize.base}px;
  -webkit-font-smoothing: antialiased;
}
a { color: ${color.accent}; }
a:hover { color: ${color.accentSoftText}; }
:focus-visible { outline: 2px solid ${color.accent}; outline-offset: 2px; }
`;

export function GlobalStyle() {
  return <style>{css}</style>;
}
