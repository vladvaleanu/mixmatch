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
import {
  useDeleteMix,
  useMix,
  useMixReport,
  useRenameMix,
  useSetEnergyShape,
  useSetMixItems,
} from '../../api/mixes';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { formatBpm, formatMinutes } from '../../ui/format';
import { PlusIcon } from '../../ui/PlusIcon';
import { Segmented } from '../../ui/Segmented';
import { useActiveMix } from './activeMixStore';
import { AddTrackDialog } from './AddTrackDialog';
import { EnergyCurve } from './EnergyCurve';
import { CARD_WIDTH, MixTrackCard } from './MixTrackCard';
import { NextSuggestions } from './NextSuggestions';
import { TransitionLink } from './TransitionLink';

type Mix = Schemas['MixOut'];
type Report = Schemas['ReportOut'];
type Track = Schemas['TrackOut'];
type Shape = Mix['energy_shape'];

const SHAPES: Shape[] = ['warmup', 'rise', 'wave', 'free'];

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

/** Cardul „Curba de energie”: forma dorită și mixul. */
function CurveCard({ mix, report }: { mix: Mix; report: Report | undefined }) {
  const setShape = useSetEnergyShape(mix.id);
  return (
    <section
      style={{
        borderRadius: radius.section,
        background: color.surface,
        border: `1px solid ${color.border}`,
        padding: space[20],
        display: 'flex',
        flexDirection: 'column',
        gap: space[14],
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: space[12],
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{ro.report.curve}</h2>
          <p
            style={{ margin: `${space[4]}px 0 0`, color: color.textMuted, fontSize: fontSize.meta }}
          >
            {mix.energy_shape === 'free' ? ro.report.curveFree : ro.report.curveHint}
          </p>
        </div>
        <Segmented
          label={ro.report.shape}
          value={mix.energy_shape}
          options={SHAPES.map((shape) => ({ value: shape, label: ro.report.shapes[shape] }))}
          onChange={(shape) => setShape.mutate(shape)}
        />
      </div>
      {report && report.energy.length > 0 && <EnergyCurve report={report} />}
    </section>
  );
}

/** Avertismentele raportului (tranzițiile „Atenție”), cu explicația venită de la server. */
function Warnings({ mixId, report }: { mixId: number; report: Report }) {
  if (report.warnings.length === 0) return null;
  return (
    <section
      aria-label={ro.report.warnings}
      style={{ display: 'flex', flexDirection: 'column', gap: space[10] }}
    >
      {report.warnings.map((warning) => (
        <div
          key={warning.position}
          role="alert"
          style={{
            borderRadius: radius.card,
            background: color.warnSoftBg,
            padding: `${space[16]}px ${space[18]}px`,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: space[14],
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke={color.warn}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            style={{ flex: 'none' }}
          >
            <path d="M12 3l9.5 17h-19z" />
            <path d="M12 10v4M12 17.5v.01" />
          </svg>
          <p style={{ margin: 0, flex: '1 1 320px', color: color.warnSoftText, lineHeight: 1.5 }}>
            {warning.message}
          </p>
          <Link
            to={`/mixuri/${mixId}/tranzitii/${warning.position}`}
            style={{
              padding: `${space[10]}px ${space[14]}px`,
              borderRadius: radius.buttonSm,
              background: color.surface3,
              color: color.warnSoftText,
              textDecoration: 'none',
              fontWeight: 500,
            }}
          >
            {ro.report.fix}
          </Link>
        </div>
      ))}
    </section>
  );
}

type OrderProps = {
  mixId: number;
  tracks: Track[];
  report: Report | undefined;
  onChange: (tracks: Track[]) => void;
  onAdd: () => void;
};

/** „Ordinea pieselor”: cardurile sortabile, cu eticheta tranziției între ele. */
function TrackOrder({ mixId, tracks, report, onChange, onAdd }: OrderProps) {
  const [dragging, setDragging] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const title = (id: unknown) => tracks.find((t) => t.id === id)?.title ?? '';
  const position = (id: unknown) => tracks.findIndex((t) => t.id === id) + 1;

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setDragging(false);
    if (!over || active.id === over.id) return;
    onChange(arrayMove(tracks, position(active.id) - 1, position(over.id) - 1));
  };

  return (
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
          onDragStart={() => setDragging(true)}
          onDragEnd={onDragEnd}
          onDragCancel={() => setDragging(false)}
          accessibility={{
            screenReaderInstructions: { draggable: ro.builder.dnd.instructions },
            announcements: {
              onDragStart: ({ active }) => ro.builder.dnd.pickedUp(title(active.id)),
              onDragOver: ({ active, over }) =>
                over ? ro.builder.dnd.over(title(active.id), position(over.id)) : undefined,
              onDragEnd: ({ active, over }) =>
                over ? ro.builder.dnd.dropped(title(active.id), position(over.id)) : undefined,
              onDragCancel: ({ active }) => ro.builder.dnd.cancelled(title(active.id)),
            },
          }}
        >
          <SortableContext items={tracks.map((t) => t.id)} strategy={horizontalListSortingStrategy}>
            <ol
              style={{
                listStyle: 'none',
                margin: 0,
                padding: 0,
                display: 'flex',
                alignItems: 'stretch',
                minWidth: 'max-content',
              }}
            >
              {tracks.map((track, i) => (
                <MixTrackCard
                  key={track.id}
                  track={track}
                  number={i + 1}
                  onRemove={() => onChange(tracks.filter((t) => t.id !== track.id))}
                  transition={
                    i > 0 ? (
                      <TransitionLink
                        // În timpul unui drag etichetele ar arăta perechi vechi: se ascund.
                        transition={dragging ? undefined : report?.transitions[i - 1]}
                        fromTitle={tracks[i - 1]?.title ?? ''}
                        toTitle={track.title}
                        to={`/mixuri/${mixId}/tranzitii/${i}`}
                      />
                    ) : undefined
                  }
                />
              ))}
              <li style={{ display: 'flex', paddingLeft: space[12] }}>
                <button
                  type="button"
                  onClick={onAdd}
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
  );
}

export function MixBuilderScreen() {
  const mixId = Number(useParams().mixId);
  const mix = useMix(mixId);
  const report = useMixReport(mixId);
  const setItems = useSetMixItems(mixId);
  const deleteMix = useDeleteMix();
  const setActive = useActiveMix((s) => s.setId);
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [confirming, setConfirming] = useState(false);

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
  // Raportul e valabil doar pentru ordinea pentru care a fost calculat.
  const current =
    report.data && report.data.track_ids.join() === tracks.map((t) => t.id).join()
      ? report.data
      : undefined;

  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexWrap: 'wrap', alignItems: 'stretch' }}>
      <div
        style={{
          flex: '999 1 560px',
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

        <CurveCard mix={data} report={current ?? report.data} />
        <TrackOrder
          mixId={data.id}
          tracks={tracks}
          report={current}
          onChange={(next) => setItems.mutate(next)}
          onAdd={() => setAdding(true)}
        />
        {current && <Warnings mixId={data.id} report={current} />}

        {adding && (
          <AddTrackDialog
            inMix={new Set(tracks.map((t) => t.id))}
            onAdd={(track) => setItems.mutate([...tracks, track])}
            onClose={() => setAdding(false)}
          />
        )}
        {confirming && (
          <Dialog title={ro.builder.deleteTitle} onClose={() => setConfirming(false)}>
            <p style={{ margin: 0, color: color.textSoft }}>
              {ro.builder.deleteConfirm(data.name)}
            </p>
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

      <aside
        style={{
          flex: '1 1 300px',
          maxWidth: 380,
          padding: `${space[28]}px ${space[24]}px`,
          borderLeft: `1px solid ${color.border}`,
        }}
      >
        <NextSuggestions
          mix={data}
          nextTargetEnergy={current?.next_target_energy ?? null}
          onAdd={(track) => setItems.mutate([...tracks, track])}
        />
      </aside>
    </div>
  );
}
