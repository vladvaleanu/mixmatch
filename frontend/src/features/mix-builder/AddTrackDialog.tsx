import { useState } from 'react';

import type { Schemas } from '../../api/client';
import { useTracks } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, size, space } from '../../theme/tokens';
import { Dialog } from '../../ui/Dialog';
import { formatBpm } from '../../ui/format';
import { KeyPill } from '../../ui/KeyPill';
import { PlusIcon } from '../../ui/PlusIcon';
import { emptyFilters } from '../library/filterStore';

type Props = {
  inMix: Set<number>;
  onAdd: (track: Schemas['TrackOut']) => void;
  onClose: () => void;
};

/** Caută în bibliotecă și adaugă piese la sfârșitul mixului. */
export function AddTrackDialog({ inMix, onAdd, onClose }: Props) {
  const [q, setQ] = useState('');
  const tracks = useTracks({ ...emptyFilters, q });

  return (
    <Dialog title={ro.builder.addTitle} onClose={onClose}>
      <input
        type="search"
        aria-label={ro.builder.addSearch}
        placeholder={ro.filters.searchPlaceholder}
        value={q}
        onChange={(event) => setQ(event.target.value)}
        style={{
          height: size.touch,
          padding: `0 ${space[14]}px`,
          borderRadius: radius.control,
          border: `1px solid ${color.borderStrong}`,
          background: color.surface2,
          color: color.text,
          font: 'inherit',
        }}
      />
      <ul
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 0,
          maxHeight: '50vh',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {tracks.data?.length === 0 && (
          <li style={{ color: color.textMuted, padding: space[8] }}>{ro.builder.noTracks}</li>
        )}
        {tracks.data?.map((track) => {
          const added = inMix.has(track.id);
          return (
            <li
              key={track.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: space[12],
                padding: `${space[8]}px 0`,
                borderTop: `1px solid ${color.border}`,
              }}
            >
              <span
                style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}
              >
                <span style={{ fontWeight: 500 }}>{track.title}</span>
                <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                  {track.artist ?? ro.library.unknownArtist}
                </span>
              </span>
              {track.bpm !== null && (
                <span style={{ color: color.textSoft, fontVariantNumeric: 'tabular-nums' }}>
                  {formatBpm(track.bpm)}
                </span>
              )}
              {track.key_camelot && <KeyPill code={track.key_camelot} name={track.key_name} />}
              {added ? (
                <span
                  style={{
                    color: color.textMuted,
                    fontSize: fontSize.meta,
                    width: 40,
                    textAlign: 'center',
                  }}
                >
                  {ro.builder.inMix}
                </span>
              ) : (
                <button
                  type="button"
                  aria-label={ro.builder.addOne(track.title)}
                  onClick={() => onAdd(track)}
                  style={{
                    width: 40,
                    height: 40,
                    flex: 'none',
                    borderRadius: radius.round,
                    border: 0,
                    background: color.control,
                    color: color.text,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <PlusIcon />
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </Dialog>
  );
}
