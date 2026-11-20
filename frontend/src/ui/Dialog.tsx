import { useEffect, useId, useRef, type ReactNode } from 'react';

import { color, font, fontSize, radius, space, zIndex } from '../theme/tokens';

type Props = {
  title: string;
  onClose: () => void;
  children: ReactNode;
};

/** Fereastră modală: Escape sau click în afară o închid; focusul intră în ea la deschidere. */
export function Dialog({ title, onClose, children }: Props) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const first = panel.current?.querySelector<HTMLElement>('input, button, [tabindex]');
    first?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      previous?.focus();
    };
  }, [onClose]);

  return (
    <div
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: zIndex.dialog,
        background: color.overlay,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: space[16],
      }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={{
          width: 'min(520px, 100%)',
          background: color.surface,
          border: `1px solid ${color.border}`,
          borderRadius: radius.section,
          padding: space[24],
          display: 'flex',
          flexDirection: 'column',
          gap: space[16],
        }}
      >
        <h2
          id={titleId}
          style={{
            margin: 0,
            fontFamily: font.display,
            fontSize: fontSize.panelTitle,
            fontWeight: 600,
          }}
        >
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}
