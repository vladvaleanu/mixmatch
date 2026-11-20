import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, coverColor, fontSize, radius, space } from '../../theme/tokens';
import { formatBpm } from '../../ui/format';
import { KeyPill } from '../../ui/KeyPill';

type Props = { track: Schemas['TrackOut']; number: number; onRemove: () => void };

export const CARD_WIDTH = 168;

function GripIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill={color.waveIdle} aria-hidden="true">
      {[6, 12, 18].map((y) => (
        <g key={y}>
          <circle cx="9" cy={y} r="1.6" />
          <circle cx="15" cy={y} r="1.6" />
        </g>
      ))}
    </svg>
  );
}

/** Cardul unei piese din mix. Se trage de mâner (mouse, atingere sau tastatură). */
export function MixTrackCard({ track, number, onRemove }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: track.id });

  return (
    <li
      ref={setNodeRef}
      style={{
        width: CARD_WIDTH,
        flex: 'none',
        padding: space[14],
        borderRadius: radius.card,
        background: color.surface2,
        border: `1px solid ${isDragging ? color.accent : color.border}`,
        display: 'flex',
        flexDirection: 'column',
        gap: space[10],
        transform: CSS.Translate.toString(transform),
        transition,
        zIndex: isDragging ? 1 : undefined,
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span
          style={{
            color: color.textMuted,
            fontSize: fontSize.label,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {number}
        </span>
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <button
            type="button"
            aria-label={ro.builder.remove(track.title)}
            onClick={onRemove}
            style={{
              border: 0,
              background: 'transparent',
              color: color.textMuted,
              cursor: 'pointer',
              padding: space[4],
              display: 'flex',
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M6 6l12 12M18 6L6 18"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
              />
            </svg>
          </button>
          <button
            type="button"
            ref={setActivatorNodeRef}
            aria-label={ro.builder.drag(track.title)}
            {...attributes}
            {...listeners}
            style={{
              border: 0,
              background: 'transparent',
              cursor: isDragging ? 'grabbing' : 'grab',
              padding: space[4],
              display: 'flex',
              touchAction: 'none',
            }}
          >
            <GripIcon />
          </button>
        </span>
      </div>
      <span
        aria-hidden="true"
        style={{
          width: 36,
          height: 36,
          borderRadius: radius.pill,
          background: coverColor(track.key_camelot),
        }}
      />
      <span style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
        <span style={{ fontWeight: 500, overflowWrap: 'anywhere' }}>{track.title}</span>
        <span style={{ color: color.textMuted, fontSize: fontSize.meta, overflowWrap: 'anywhere' }}>
          {track.artist ?? ro.library.unknownArtist}
        </span>
      </span>
      <span
        style={{
          marginTop: 'auto',
          display: 'flex',
          gap: space[6],
          alignItems: 'center',
          fontSize: fontSize.label,
          color: color.textSoft,
        }}
      >
        {track.bpm !== null && (
          <span style={{ fontVariantNumeric: 'tabular-nums' }}>{formatBpm(track.bpm)}</span>
        )}
        {track.key_camelot && <KeyPill code={track.key_camelot} name={track.key_name} />}
        {track.energy !== null && <span>· E{track.energy}</span>}
      </span>
    </li>
  );
}
