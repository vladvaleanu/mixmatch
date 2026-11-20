import { useState, type DragEvent } from 'react';

import { useUploadTracks } from '../../api/library';
import type { TrackFilters } from '../../api/tracks';
import { useTracks } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, radius, space } from '../../theme/tokens';
import { ScreenHeader } from '../../ui/ScreenHeader';
import { AddFolderDialog } from './AddFolderDialog';
import { AnalysisBanner } from './AnalysisBanner';
import { droppedAudioFiles } from './dropFiles';
import { useAddFolderDialog } from './addFolderStore';
import { hasActiveFilters, useFilters } from './filterStore';
import { useSelectedTrack } from './selectionStore';
import { Sidebar } from './Sidebar';
import { TrackPanel } from './TrackPanel';
import { TrackTable } from './TrackTable';
import { UploadDialog } from './UploadDialog';

function FolderIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 16V4M7 9l5-5 5 5" />
      <path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
    </svg>
  );
}

const SORTS: TrackFilters['sort'][] = ['title', 'bpm', 'key', 'energy', 'duration', 'recent'];

export function LibraryScreen() {
  const { filters, set, reset } = useFilters();
  const tracks = useTracks(filters);
  const library = useTracks(); // toată biblioteca: piesa selectată rămâne în panou și când e filtrată
  const { open, setOpen } = useAddFolderDialog();
  const selectedId = useSelectedTrack((s) => s.id);
  const selected = library.data?.find((track) => track.id === selectedId);
  const count = tracks.data?.length ?? 0;
  const filtered = hasActiveFilters(filters);
  const upload = useUploadTracks();
  const [dragging, setDragging] = useState(false);
  const [dropped, setDropped] = useState<number | null>(null);

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    void droppedAudioFiles(event.dataTransfer).then((files) => {
      setDropped(files.length);
      if (files.length) upload.mutate(files);
    });
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', flex: 1, minWidth: 0, alignItems: 'stretch' }}>
      <aside
        style={{
          flex: '1 1 220px',
          maxWidth: 260,
          padding: space[24],
          borderRight: `1px solid ${color.border}`,
        }}
      >
        <Sidebar selected={selected} />
      </aside>

      <div
        style={{
          flex: '999 1 560px',
          minWidth: 0,
          padding: space[28],
          display: 'flex',
          flexDirection: 'column',
          gap: space[20],
        }}
      >
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: space[12],
          }}
        >
          <ScreenHeader title={ro.library.title} subtitle={ro.library.subtitle} />
          <div style={{ display: 'flex', gap: space[8], color: color.textMuted }}>
            {tracks.data && (
              <span
                style={{
                  padding: `${space[8]}px ${space[12]}px`,
                  borderRadius: radius.round,
                  background: color.surface2,
                }}
              >
                {ro.library.trackCount(count)}
              </span>
            )}
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: space[4],
                padding: `0 ${space[12]}px`,
                borderRadius: radius.round,
                background: color.surface2,
              }}
            >
              {ro.filters.sortedBy}
              <select
                value={filters.sort}
                onChange={(event) => set({ sort: event.target.value as TrackFilters['sort'] })}
                style={{
                  border: 0,
                  background: 'transparent',
                  color: color.text,
                  font: 'inherit',
                  cursor: 'pointer',
                }}
              >
                {SORTS.map((sort) => (
                  <option key={sort} value={sort}>
                    {ro.filters.sort[sort]}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setOpen(true)}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          style={{
            border: `1.5px dashed ${dragging ? color.accent : color.borderDashed}`,
            borderRadius: radius.card,
            padding: `${space[18]}px ${space[20]}px`,
            display: 'flex',
            alignItems: 'center',
            gap: space[14],
            background: dragging ? color.accentTint : 'transparent',
            color: dragging ? color.accentSoftText : color.textMuted,
            font: 'inherit',
            textAlign: 'left',
            cursor: 'pointer',
          }}
        >
          <FolderIcon />
          {dragging ? ro.library.dropNow : ro.library.addFolderZone}
        </button>

        <AnalysisBanner />

        {tracks.isPending ? (
          <p style={{ margin: 0, color: color.textMuted }}>{ro.library.loading}</p>
        ) : count > 0 ? (
          <TrackTable tracks={tracks.data ?? []} />
        ) : filtered ? (
          <p style={{ margin: 0, color: color.textMuted }}>
            {ro.filters.noResults}{' '}
            <button
              type="button"
              onClick={reset}
              style={{
                border: 0,
                padding: 0,
                background: 'transparent',
                color: color.accent,
                font: 'inherit',
                cursor: 'pointer',
              }}
            >
              {ro.filters.reset}
            </button>
          </p>
        ) : (
          <p style={{ margin: 0, color: color.textMuted }}>{ro.library.empty}</p>
        )}

        {open && <AddFolderDialog onClose={() => setOpen(false)} />}
        {dropped !== null && (
          <UploadDialog
            count={dropped}
            result={upload.data}
            pending={upload.isPending}
            onClose={() => {
              setDropped(null);
              upload.reset();
            }}
          />
        )}
      </div>

      <aside
        style={{
          flex: '1 1 300px',
          maxWidth: 380,
          padding: `${space[28]}px ${space[24]}px`,
          borderLeft: `1px solid ${color.border}`,
        }}
      >
        <TrackPanel track={selected} />
      </aside>
    </div>
  );
}
