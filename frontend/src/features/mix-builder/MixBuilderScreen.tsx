import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  horizontalListSortingStrategy,
  SortableContext,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import type { Schemas } from '../../api/client';
import { useDeleteMix, useMix, useRenameMix, useSetMixItems } from '../../api/mixes';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { formatBpm, formatMinutes } from '../../ui/format';
import { PlusIcon } from '../../ui/PlusIcon';
import { useActiveMix } from './activeMixStore';
import { AddTrackDialog } from './AddTrackDialog';
import { CARD_WIDTH, MixTrackCard } from './MixTrackCard';

type Mix = Schemas['MixOut'];

function title(mix: Mix, id: unknown): string {
  return mix.tracks.find((t) => t.id === id)?.title ?? '';
}

function MixName({ mix }: { mix: Mix }) {
  const rename = useRenameMix(mix.id);
  const [name, setName] = useState(mix.name);
  const [savedName, setSavedName] = useState(mix.name);
  if (mix.name !== savedName) {
    setSavedName(mix.name);
    setName(mix.name);
  }
  const save = () => {
    const trimmed = name.trim();
    if (!trimmed) setName(mix.name);
    else if (trimmed !== mix.name) rename.mutate(trimmed);
  };
  return (
    <input
      aria-label={ro.builder.name}
      value={name}
      onChange={(event) => setName(event.target.value)}
      onBlur={save}
      onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()}
      style={{
        margin: 0,
        padding: 0,
        width: '100%',
        border: 0,
        borderBottom: `1px dashed transparent`,
        background: 'transparent',
        color: color.text,
        fontFamily: font.display,
        fontSize: fontSize.h1,
        fontWeight: 600,
        letterSpacing: '-0.02em',
      }}
    />
  );
}

export function MixBuilderScreen() {
  const mixId = Number(useParams().mixId);
  const mix = useMix(mixId);
  const setItems = useSetMixItems(mixId);
  const deleteMix = useDeleteMix();
  const setActive = useActiveMix((s) => s.setId);
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  useEffect(() => {
    if (mix.data) setActive(mix.data.id); // „Adaugă în mix” din Bibliotecă țintește mixul deschis
  }, [mix.data, setActive]);

  if (mix.isError) {
    return (
      <div style={{ padding: space[28], display: 'flex', flexDirection: 'column', gap: space[12] }}>
        <p style={{ margin: 0, color: color.textMuted }}>{ro.builder.notFound}</p>
        <Link to="/mixuri" style={{ color: color.accent }}>
          {ro.builder.back}
        </Link>
      </div>
    );
  }
  if (!mix.data) return null;
  const data = mix.data;
  const tracks = data.tracks;
  const first = tracks[0]?.bpm;
  const last = tracks[tracks.length - 1]?.bpm;

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const from = tracks.findIndex((t) => t.id === active.id);
    const to = tracks.findIndex((t) => t.id === over.id);
    setItems.mutate(arrayMove(tracks, from, to));
  };

  return (
    <div
      style={{
        flex: 1,
        minWidth: 0,
        padding: space[28],
        display: 'flex',
        flexDirection: 'column',
        gap: space[22],
      }}
    >
      <Link to="/mixuri" style={{ color: color.textMuted, fontSize: fontSize.meta }}>
        ← {ro.builder.back}
      </Link>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          gap: space[16],
        }}
      >
        <div style={{ flex: '1 1 320px', minWidth: 0 }}>
          <MixName mix={data} />
          <p style={{ margin: `${space[6]}px 0 0`, color: color.textMuted }}>
            {ro.mixes.meta(tracks.length, formatMinutes(data.duration_s))}
            {first != null &&
              last != null &&
              ` · ${ro.mixes.bpmRange(formatBpm(first), formatBpm(last))}`}
          </p>
        </div>
        <Button onClick={() => setConfirming(true)}>{ro.builder.delete}</Button>
      </div>

      <section style={{ display: 'flex', flexDirection: 'column', gap: space[12] }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
            gap: space[12],
          }}
        >
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{ro.builder.order}</h2>
          {tracks.length > 1 && (
            <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
              {ro.builder.dragHint}
            </span>
          )}
        </div>
        {tracks.length === 0 && (
          <p style={{ margin: 0, color: color.textMuted }}>{ro.builder.empty}</p>
        )}
        <div style={{ overflowX: 'auto', paddingBottom: space[6] }}>
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={onDragEnd}
            accessibility={{
              screenReaderInstructions: { draggable: ro.builder.dnd.instructions },
              announcements: {
                onDragStart: ({ active }) => ro.builder.dnd.pickedUp(title(data, active.id)),
                onDragOver: ({ active, over }) =>
                  over
                    ? ro.builder.dnd.over(
                        title(data, active.id),
                        tracks.findIndex((t) => t.id === over.id) + 1,
                      )
                    : undefined,
                onDragEnd: ({ active, over }) =>
                  over
                    ? ro.builder.dnd.dropped(
                        title(data, active.id),
                        tracks.findIndex((t) => t.id === over.id) + 1,
                      )
                    : undefined,
                onDragCancel: ({ active }) => ro.builder.dnd.cancelled(title(data, active.id)),
              },
            }}
          >
            <SortableContext
              items={tracks.map((t) => t.id)}
              strategy={horizontalListSortingStrategy}
            >
              <ol
                style={{
                  listStyle: 'none',
                  margin: 0,
                  padding: 0,
                  display: 'flex',
                  alignItems: 'stretch',
                  gap: space[12],
                  minWidth: 'max-content',
                }}
              >
                {tracks.map((track, i) => (
                  <MixTrackCard
                    key={track.id}
                    track={track}
                    number={i + 1}
                    onRemove={() => setItems.mutate(tracks.filter((t) => t.id !== track.id))}
                  />
                ))}
                <li style={{ display: 'flex' }}>
                  <button
                    type="button"
                    onClick={() => setAdding(true)}
                    style={{
                      width: 120,
                      minHeight: CARD_WIDTH,
                      borderRadius: radius.card,
                      border: `1.5px dashed ${color.borderDashed}`,
                      background: 'transparent',
                      color: color.textMuted,
                      font: 'inherit',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: space[8],
                      cursor: 'pointer',
                    }}
                  >
                    <PlusIcon />
                    {ro.builder.add}
                  </button>
                </li>
              </ol>
            </SortableContext>
          </DndContext>
        </div>
      </section>

      {adding && (
        <AddTrackDialog
          inMix={new Set(tracks.map((t) => t.id))}
          onAdd={(track) => setItems.mutate([...tracks, track])}
          onClose={() => setAdding(false)}
        />
      )}
      {confirming && (
        <Dialog title={ro.builder.deleteTitle} onClose={() => setConfirming(false)}>
          <p style={{ margin: 0, color: color.textSoft }}>{ro.builder.deleteConfirm(data.name)}</p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: space[8] }}>
            <Button onClick={() => setConfirming(false)}>{ro.common.cancel}</Button>
            <Button
              variant="primary"
              onClick={() =>
                deleteMix.mutate(data.id, {
                  onSuccess: () => {
                    setActive(null);
                    navigate('/mixuri');
                  },
                })
              }
            >
              {ro.builder.delete}
            </Button>
          </div>
        </Dialog>
      )}
    </div>
  );
}
