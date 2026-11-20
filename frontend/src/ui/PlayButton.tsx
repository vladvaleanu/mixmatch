import { color, radius } from '../theme/tokens';

type Props = { playing: boolean; label: string; onClick: () => void; size?: number };

/** Butonul rotund de play/pauză (fundal `control`). */
export function PlayButton({ playing, label, onClick, size = 36 }: Props) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={playing}
      onClick={(event) => {
        event.stopPropagation(); // în tabel, click-ul pe play nu selectează și rândul
        onClick();
      }}
      style={{
        width: size,
        height: size,
        borderRadius: radius.round,
        border: 0,
        background: playing ? color.accent : color.control,
        color: playing ? color.accentText : color.text,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        flex: 'none',
      }}
    >
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        {playing ? (
          <path d="M2.5 1.5h2.5v9H2.5zM7 1.5h2.5v9H7z" fill="currentColor" />
        ) : (
          <path d="M3 1.5v9l7.5-4.5z" fill="currentColor" />
        )}
      </svg>
    </button>
  );
}
