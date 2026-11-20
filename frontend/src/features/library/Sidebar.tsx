import { useState, type CSSProperties } from 'react';

import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, fontSize, keyColor, radius, size, space } from '../../theme/tokens';
import { hasActiveFilters, useFilters } from './filterStore';

const KEY_CODES = Array.from({ length: 12 }, (_, i) => [`${i + 1}A`, `${i + 1}B`]).flat();

const heading = {
  margin: 0,
  fontSize: fontSize.label,
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: color.textMuted,
} satisfies CSSProperties;

const field = {
  height: 40,
  borderRadius: radius.buttonSm,
  border: `1px solid ${color.borderStrong}`,
  background: color.surface2,
  color: color.text,
  font: 'inherit',
} satisfies CSSProperties;

function toggleStyle(active: boolean): CSSProperties {
  return {
    ...field,
    flex: 1,
    border: active ? 0 : field.border,
    background: active ? color.accentSoftBgStrong : color.surface2,
    color: active ? color.accentSoftText : color.textSoft,
    cursor: 'pointer',
  };
}

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

function parseBpm(value: string): number | null {
  const n = Number.parseFloat(value.replace(',', '.'));
  return Number.isFinite(n) ? n : null;
}

type Props = { selected: Schemas['TrackOut'] | undefined };

export function Sidebar({ selected }: Props) {
  const { filters, set, reset } = useFilters();
  const [pickerOpen, setPickerOpen] = useState(false);
  const canCompare = Boolean(selected?.analyzed && selected.key_camelot);
  const comparing = filters.compatible_with !== null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[28] }}>
      <section style={{ display: 'flex', flexDirection: 'column', gap: space[12] }}>
        <h2 style={heading}>{ro.filters.title}</h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
          <span style={{ color: color.textSoft }}>{ro.filters.tempo}</span>
          <div style={{ display: 'flex', gap: space[8] }}>
            {(['bpm_min', 'bpm_max'] as const).map((name) => (
              <input
                key={name}
                aria-label={name === 'bpm_min' ? ro.filters.bpmMin : ro.filters.bpmMax}
                inputMode="decimal"
                placeholder={name === 'bpm_min' ? 'min' : 'max'}
                value={filters[name] ?? ''}
                onChange={(event) => set({ [name]: parseBpm(event.target.value) })}
                style={{ ...field, width: '100%', minWidth: 0, padding: `0 ${space[10]}px` }}
              />
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
          <span style={{ color: color.textSoft }}>{ro.filters.energy}</span>
          <div style={{ display: 'flex', gap: space[6] }}>
            {[1, 2, 3, 4, 5].map((level) => (
              <button
                key={level}
                type="button"
                aria-label={ro.filters.energyLevel(level)}
                aria-pressed={filters.energy.includes(level)}
                onClick={() => set({ energy: toggle(filters.energy, level) })}
                style={toggleStyle(filters.energy.includes(level))}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
          <span style={{ color: color.textSoft }}>{ro.filters.key}</span>
          <button
            type="button"
            aria-expanded={pickerOpen}
            onClick={() => setPickerOpen(!pickerOpen)}
            style={{
              ...toggleStyle(filters.key.length > 0),
              flex: 'none',
              textAlign: 'left',
              padding: `0 ${space[12]}px`,
            }}
          >
            {filters.key.length ? ro.filters.keysChosen(filters.key) : ro.filters.anyKey}
          </button>
          {pickerOpen && (
            <div
              role="group"
              aria-label={ro.filters.keyPicker}
              style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: space[4] }}
            >
              {KEY_CODES.map((code) => {
                const on = filters.key.includes(code);
                return (
                  <button
                    key={code}
                    type="button"
                    aria-pressed={on}
                    onClick={() => set({ key: toggle(filters.key, code) })}
                    style={{
                      height: 32,
                      borderRadius: radius.pill,
                      border: on ? 0 : `1px solid ${color.borderStrong}`,
                      background: on ? keyColor(code) : 'transparent',
                      color: on ? color.accentText : color.textSoft,
                      font: 'inherit',
                      fontSize: fontSize.meta,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {code}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: space[10],
            minHeight: size.touch,
            color: canCompare || comparing ? color.textSoft : color.textMuted,
          }}
        >
          <input
            type="checkbox"
            checked={comparing}
            disabled={!canCompare && !comparing}
            onChange={(event) =>
              set({ compatible_with: event.target.checked && selected ? selected.id : null })
            }
            style={{ width: 18, height: 18, accentColor: color.accent }}
          />
          {selected && (canCompare || comparing)
            ? ro.filters.compatibleWith(selected.title)
            : ro.filters.compatibleHint}
        </label>

        {hasActiveFilters(filters) && (
          <button
            type="button"
            onClick={reset}
            style={{
              alignSelf: 'flex-start',
              border: 0,
              background: 'transparent',
              color: color.accent,
              font: 'inherit',
              padding: 0,
              cursor: 'pointer',
            }}
          >
            {ro.filters.reset}
          </button>
        )}
      </section>

      <p
        style={{
          margin: 0,
          padding: space[14],
          borderRadius: radius.control,
          background: color.surface2,
          color: color.textMuted,
          lineHeight: 1.5,
          fontSize: fontSize.meta,
        }}
      >
        {ro.filters.local}
      </p>
    </div>
  );
}
