import { useTracks } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, radius, space } from '../../theme/tokens';
import { ScreenHeader } from '../../ui/ScreenHeader';
import { AddFolderDialog } from './AddFolderDialog';
import { useAddFolderDialog } from './addFolderStore';
import { TrackTable } from './TrackTable';

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

export function LibraryScreen() {
  const tracks = useTracks();
  const { open, setOpen } = useAddFolderDialog();
  const count = tracks.data?.length ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[20] }}>
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
        {tracks.data && (
          <span
            style={{
              padding: `${space[8]}px ${space[12]}px`,
              borderRadius: radius.round,
              background: color.surface2,
              color: color.textMuted,
            }}
          >
            {ro.library.trackCount(count)}
          </span>
        )}
      </div>

      <button
        type="button"
        onClick={() => setOpen(true)}
        style={{
          border: `1.5px dashed ${color.borderDashed}`,
          borderRadius: radius.card,
          padding: `${space[18]}px ${space[20]}px`,
          display: 'flex',
          alignItems: 'center',
          gap: space[14],
          background: 'transparent',
          color: color.textMuted,
          font: 'inherit',
          textAlign: 'left',
          cursor: 'pointer',
        }}
      >
        <FolderIcon />
        {ro.library.addFolderZone}
      </button>

      {tracks.isPending ? (
        <p style={{ margin: 0, color: color.textMuted }}>{ro.library.loading}</p>
      ) : count === 0 ? (
        <p style={{ margin: 0, color: color.textMuted }}>{ro.library.empty}</p>
      ) : (
        <TrackTable tracks={tracks.data ?? []} />
      )}

      {open && <AddFolderDialog onClose={() => setOpen(false)} />}
    </div>
  );
}
