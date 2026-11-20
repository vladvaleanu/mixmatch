import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ro } from '../../i18n/ro';
import { color, radius, size, space } from '../../theme/tokens';
import { useFilters } from './filterStore';

const DEBOUNCE_MS = 250;

/** Căutarea din bara de sus: filtrează Biblioteca după titlu și artist. */
export function LibrarySearch() {
  const q = useFilters((s) => s.filters.q);
  const set = useFilters((s) => s.set);
  const [text, setText] = useState(q);
  const navigate = useNavigate();
  const location = useLocation();

  // „Șterge filtrele” golește și câmpul: când `q` se schimbă din afară, textul îl urmează.
  const [lastQ, setLastQ] = useState(q);
  if (q !== lastQ) {
    setLastQ(q);
    setText(q);
  }

  useEffect(() => {
    if (text === q) return;
    const timer = window.setTimeout(() => set({ q: text }), DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [text, q, set]);

  return (
    <label
      style={{
        flex: '1 1 260px',
        display: 'flex',
        alignItems: 'center',
        gap: space[10],
        height: size.touch,
        padding: `0 ${space[14]}px`,
        borderRadius: radius.control,
        border: `1px solid ${color.borderStrong}`,
        background: color.surface2,
      }}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke={color.textMuted}
        strokeWidth="2"
        strokeLinecap="round"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="M20 20l-3.5-3.5" />
      </svg>
      <input
        id="library-search"
        type="search"
        aria-label={ro.filters.search}
        placeholder={ro.filters.searchPlaceholder}
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          if (location.pathname !== '/biblioteca') navigate('/biblioteca');
        }}
        style={{
          flex: 1,
          minWidth: 0,
          border: 0,
          outline: 'none',
          background: 'transparent',
          color: color.text,
          font: 'inherit',
        }}
      />
    </label>
  );
}
