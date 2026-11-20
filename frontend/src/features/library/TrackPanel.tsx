import type { ReactNode } from 'react';

import type { Schemas } from '../../api/client';
import { trackAudioUrl, useSetEnergy, useWaveform } from '../../api/tracks';
import { player, usePlayer } from '../../audio/engine';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, space } from '../../theme/tokens';
import { EnergyDots } from '../../ui/EnergyDots';
import { formatBpm, formatDuration } from '../../ui/format';
import { Waveform } from '../../ui/Waveform';
import { AddToMixButton } from './AddToMixButton';
import { CollectionToggles } from './CollectionToggles';
import { MatchList } from './MatchList';
import { TrackPlayButton } from './TrackPlayButton';

type Track = Schemas['TrackOut'];

const label = {
  fontSize: fontSize.label,
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: color.textMuted,
} as const;

function Tile({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ padding: space[12], borderRadius: radius.control, background: color.surface2 }}>
      <div style={{ color: color.textMuted, fontSize: fontSize.label }}>{title}</div>
      <div style={{ marginTop: space[4], fontWeight: 500 }}>{children}</div>
    </div>
  );
}

const WAVE_BARS = 72;

export function TrackPanel({ track }: { track: Track | undefined }) {
  const waveform = useWaveform(track?.id ?? null);
  const setEnergy = useSetEnergy();
  const progress = usePlayer((s) =>
    track && s.trackId === track.id && s.durationS > 0 ? s.positionS / s.durationS : undefined,
  );
  const position = usePlayer((s) => (track && s.trackId === track.id ? s.positionS : 0));

  if (!track) {
    return <p style={{ margin: 0, color: color.textMuted }}>{ro.panel.empty}</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[22] }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: space[4] }}>
        <span style={label}>{ro.panel.selected}</span>
        <span style={{ fontFamily: font.display, fontSize: fontSize.panelTitle, fontWeight: 600 }}>
          {track.title}
        </span>
        <span style={{ color: color.textMuted }}>{track.artist ?? ro.library.unknownArtist}</span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: 64,
          padding: `0 ${space[4]}px`,
          borderRadius: radius.control,
          background: color.surface2,
          overflow: 'hidden',
        }}
      >
        {waveform.data && (
          <Waveform
            peaks={waveform.data.peaks}
            bars={WAVE_BARS}
            height={52}
            progress={progress ?? 0}
            onSeek={(fraction) =>
              player.playFrom(
                track.id,
                trackAudioUrl(track.id),
                track.duration_s,
                fraction * track.duration_s,
              )
            }
          />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: space[12] }}>
        <TrackPlayButton track={track} size={44} />
        <span style={{ color: color.textSoft, fontVariantNumeric: 'tabular-nums' }}>
          {formatDuration(position)} / {formatDuration(track.duration_s)}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
          gap: space[10],
        }}
      >
        <Tile title={ro.panel.tempo}>
          {track.bpm !== null ? ro.panel.bpm(formatBpm(track.bpm)) : ro.panel.unknown}
        </Tile>
        <Tile title={ro.panel.key}>
          {track.key_camelot ? `${track.key_camelot} · ${track.key_name}` : ro.panel.unknown}
        </Tile>
        <Tile title={ro.panel.energy}>
          {track.energy !== null ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: space[8] }}>
              {ro.panel.energyOf(track.energy)}
              <EnergyDots
                value={track.energy}
                manual={track.energy_manual !== null}
                onChange={(energy) => setEnergy.mutate({ id: track.id, energy })}
              />
            </span>
          ) : (
            ro.panel.unknown
          )}
        </Tile>
        <Tile title={ro.panel.introOutro}>
          {track.intro_bars !== null && track.outro_bars !== null
            ? ro.panel.bars(track.intro_bars, track.outro_bars)
            : ro.panel.unknown}
        </Tile>
      </div>

      <AddToMixButton track={track} />

      <CollectionToggles track={track} />

      <MatchList track={track} />
    </div>
  );
}
