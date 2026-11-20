import { useEffect, useState } from 'react';

import { ro } from '../i18n/ro';
import { color, fontSize, radius, space } from '../theme/tokens';
import { Dialog } from './Dialog';
import { isTyping } from './isTyping';

const KEYS: [string, string][] = [
  ['Spațiu', ro.shortcuts.play],
  ['↑ ↓ / K J', ro.shortcuts.move],
  ['/', ro.shortcuts.search],
  ['?', ro.shortcuts.help],
  ['Esc', ro.shortcuts.close],
];

/** Butonul „?” din bara de sus și lista scurtăturilor (se deschide și cu tasta „?”). */
export function ShortcutsHelp() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === '?' && !isTyping(event.target)) {
        event.preventDefault();
        setOpen(true);
      }
      if (event.key === '/' && !isTyping(event.target)) {
        const search = document.getElementById('library-search');
        if (search) {
          event.preventDefault();
          search.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        aria-label={ro.shortcuts.title}
        title={ro.shortcuts.title}
        onClick={() => setOpen(true)}
        style={{
          width: 40,
          height: 40,
          borderRadius: radius.round,
          border: `1px solid ${color.borderStrong}`,
          background: color.surface2,
          color: color.textSoft,
          font: 'inherit',
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        ?
      </button>
      {open && (
        <Dialog title={ro.shortcuts.title} onClose={() => setOpen(false)}>
          <dl
            style={{
              margin: 0,
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: `${space[10]}px ${space[16]}px`,
            }}
          >
            {KEYS.map(([key, what]) => (
              <div key={key} style={{ display: 'contents' }}>
                <dt>
                  <kbd
                    style={{
                      padding: `${space[4]}px ${space[8]}px`,
                      borderRadius: radius.pill,
                      background: color.surface3,
                      border: `1px solid ${color.borderStrong}`,
                      fontFamily: 'inherit',
                      fontSize: fontSize.meta,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {key}
                  </kbd>
                </dt>
                <dd style={{ margin: 0, color: color.textSoft }}>{what}</dd>
              </div>
            ))}
          </dl>
        </Dialog>
      )}
    </>
  );
}
