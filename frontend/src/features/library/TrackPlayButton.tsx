import type { Schemas } from '../../api/client';
import { trackAudioUrl } from '../../api/tracks';
import { player, usePlayer } from '../../audio/engine';
import { ro } from '../../i18n/ro';
import { PlayButton } from '../../ui/PlayButton';

type Props = { track: Schemas['TrackOut']; size?: number };

export function TrackPlayButton({ track, size }: Props) {
  const playing = usePlayer((s) => s.trackId === track.id && s.playing);
  return (
    <PlayButton
      size={size}
      playing={playing}
      label={playing ? ro.player.pause(track.title) : ro.player.play(track.title)}
      onClick={() => player.toggle(track.id, trackAudioUrl(track.id), track.duration_s)}
    />
  );
}
