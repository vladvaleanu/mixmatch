import { useEffect } from 'react';

import type { Schemas } from '../../api/client';
import { trackAudioUrl } from '../../api/tracks';
import { player } from '../../audio/engine';
import { isTyping } from '../../ui/isTyping';
import { useSelectedTrack } from './selectionStore';

/** Spațiu = play/pauză pe piesa selectată; săgeți (sau J/K) = piesa următoare/anterioară. */
export function useLibraryShortcuts(tracks: Schemas['TrackOut'][] | undefined) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (!tracks?.length || isTyping(event.target) || event.metaKey || event.ctrlKey) return;
      const { id, select } = useSelectedTrack.getState();
      const index = tracks.findIndex((t) => t.id === id);
      const step = { ArrowDown: 1, j: 1, ArrowUp: -1, k: -1 }[event.key];
      if (step !== undefined) {
        event.preventDefault();
        const next = tracks[Math.min(Math.max(index + step, 0), tracks.length - 1)];
        if (next) {
          select(next.id);
          document.getElementById(`track-row-${next.id}`)?.scrollIntoView({ block: 'nearest' });
        }
      } else if (event.key === ' ' && index >= 0) {
        const track = tracks[index];
        if (!track) return;
        event.preventDefault();
        player.toggle(track.id, trackAudioUrl(track.id), track.duration_s);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [tracks]);
}
