import { useState, type CSSProperties } from 'react';

import { useCollections, useCreateCollection, useDeleteCollection } from '../../api/collections';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { useFilters } from './filterStore';

const heading = {
  margin: 0,
  fontSize: fontSize.label,
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: color.textMuted,
} satisfies CSSProperties;

function item(active: boolean): CSSProperties {
  return {
    flex: 1,
    minWidth: 0,
    padding: `${space[10]}px ${space[12]}px`,
    borderRadius: radius.buttonSm,
    border: 0,
    background: active ? color.surface2 : 'transparent',
    color: active ? color.text : color.textSoft,
    font: 'inherit',
    textAlign: 'left',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    gap: space[8],
  };
}

/** „Colecții” din bara laterală: toate piesele, adăugate recent și colecțiile utilizatorului. */
export function CollectionsNav() {
  const { filters, set } = useFilters();
  const collections = useCollections();
  const create = useCreateCollection();
  const remove = useDeleteCollection();
  const [naming, setNaming] = useState<string | null>(null);
  const [removing, setRemoving] = useState<{ id: number; name: string } | null>(null);
  const c = ro.collections;

  const allActive = filters.collection === null && filters.sort !== 'recent';
  const recentActive = filters.collection === null && filters.sort === 'recent';

  const submit = () => {
    const name = naming?.trim();
    if (name) create.mutate(name, { onSuccess: (made) => set({ collection: made.id }) });
    setNaming(null);
  };

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
      <h2 style={{ ...heading, marginBottom: space[4] }}>{c.title}</h2>
      <button
        type="button"
        aria-pressed={allActive}
        onClick={() =>
          set({ collection: null, sort: filters.sort === 'recent' ? 'title' : filters.sort })
        }
        style={item(allActive)}
      >
        {c.all}
      </button>
      <button
        type="button"
        aria-pressed={recentActive}
        onClick={() => set({ collection: null, sort: 'recent' })}
        style={item(recentActive)}
      >
        {c.recent}
      </button>
      {collections.data?.map((collection) => {
        const active = filters.collection === collection.id;
        return (
          <span key={collection.id} style={{ display: 'flex', alignItems: 'center' }}>
            <button
              type="button"
              aria-pressed={active}
              onClick={() => set({ collection: collection.id })}
              style={item(active)}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {collection.name}
              </span>
              <span style={{ color: color.textMuted, fontVariantNumeric: 'tabular-nums' }}>
                {collection.track_count}
              </span>
            </button>
            <button
              type="button"
              aria-label={c.remove(collection.name)}
              onClick={() => setRemoving(collection)}
              style={{
                border: 0,
                background: 'transparent',
                color: color.textMuted,
                cursor: 'pointer',
                padding: space[8],
                display: 'flex',
              }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M6 6l12 12M18 6L6 18"
                  stroke="currentColor"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </span>
        );
      })}
      {naming === null ? (
        <button
          type="button"
          onClick={() => setNaming('')}
          style={{ ...item(false), color: color.accent }}
        >
          {c.create}
        </button>
      ) : (
        <input
          autoFocus
          aria-label={c.nameLabel}
          placeholder={c.namePlaceholder}
          value={naming}
          onChange={(event) => setNaming(event.target.value)}
          onBlur={submit}
          onKeyDown={(event) => {
            if (event.key === 'Enter') submit();
            if (event.key === 'Escape') setNaming(null);
          }}
          style={{
            height: 40,
            padding: `0 ${space[10]}px`,
            borderRadius: radius.buttonSm,
            border: `1px solid ${color.borderStrong}`,
            background: color.surface2,
            color: color.text,
            font: 'inherit',
          }}
        />
      )}
      {removing && (
        <Dialog title={c.removeTitle} onClose={() => setRemoving(null)}>
          <p style={{ margin: 0, color: color.textSoft }}>{c.removeConfirm(removing.name)}</p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: space[8] }}>
            <Button onClick={() => setRemoving(null)}>{ro.common.cancel}</Button>
            <Button
              variant="primary"
              onClick={() => {
                remove.mutate(removing.id);
                if (filters.collection === removing.id) set({ collection: null });
                setRemoving(null);
              }}
            >
              {c.removeTitle}
            </Button>
          </div>
        </Dialog>
      )}
    </section>
  );
}
