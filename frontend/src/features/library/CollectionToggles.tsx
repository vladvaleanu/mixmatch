import type { Schemas } from '../../api/client';
import { useCollections, useToggleCollection } from '../../api/collections';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, space } from '../../theme/tokens';

/** În panoul piesei: în ce colecții e; click o pune sau o scoate. */
export function CollectionToggles({ track }: { track: Schemas['TrackOut'] }) {
  const collections = useCollections();
  const toggle = useToggleCollection();
  const member = new Set(track.collection_ids);
  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: space[8] }}>
      <h2
        style={{
          margin: 0,
          fontSize: fontSize.label,
          fontWeight: 600,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: color.textMuted,
        }}
      >
        {ro.collections.inPanel}
      </h2>
      {collections.data?.length === 0 ? (
        <p style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta }}>
          {ro.collections.none}
        </p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: space[6] }}>
          {collections.data?.map((collection) => {
            const on = member.has(collection.id);
            return (
              <button
                key={collection.id}
                type="button"
                aria-pressed={on}
                aria-label={ro.collections.toggle(collection.name)}
                onClick={() =>
                  toggle.mutate({ collectionId: collection.id, trackId: track.id, member: !on })
                }
                style={{
                  padding: `${space[6]}px ${space[12]}px`,
                  borderRadius: radius.round,
                  border: on ? 0 : `1px solid ${color.borderStrong}`,
                  background: on ? color.accentSoftBgStrong : 'transparent',
                  color: on ? color.accentSoftText : color.textSoft,
                  font: 'inherit',
                  fontSize: fontSize.meta,
                  cursor: 'pointer',
                }}
              >
                {collection.name}
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
