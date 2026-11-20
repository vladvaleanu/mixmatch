// Singurul loc din aplicație care atinge Web Audio și elementul <audio>.
// Un singur player pentru toată aplicația: o piesă nouă o oprește pe cea veche.
import { create } from 'zustand';

import { ro } from '../i18n/ro';
import { showToast } from '../ui/toastStore';

export type PlayerState = {
  trackId: number | null;
  playing: boolean;
  positionS: number;
  durationS: number;
};

export const usePlayer = create<PlayerState>(() => ({
  trackId: null,
  playing: false,
  positionS: 0,
  durationS: 0,
}));

let element: HTMLAudioElement | null = null;
let context: AudioContext | null = null;
let frame = 0;

function tick() {
  if (!element) return;
  usePlayer.setState({ positionS: element.currentTime });
  frame = requestAnimationFrame(tick);
}

function audioElement(): HTMLAudioElement {
  if (element) return element;
  const audio = new Audio();
  audio.preload = 'auto';
  // Trece prin AudioContext ca pașii următori (tranziții, câștig) să aibă unde să se lege.
  if (typeof AudioContext !== 'undefined') {
    context = new AudioContext();
    context.createMediaElementSource(audio).connect(context.destination);
  }
  audio.addEventListener('play', () => {
    usePlayer.setState({ playing: true });
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(tick);
  });
  const stopped = () => {
    usePlayer.setState({ playing: false, positionS: audio.currentTime });
    cancelAnimationFrame(frame);
  };
  audio.addEventListener('pause', stopped);
  audio.addEventListener('ended', stopped);
  audio.addEventListener('loadedmetadata', () => {
    usePlayer.setState({ durationS: Number.isFinite(audio.duration) ? audio.duration : 0 });
  });
  audio.addEventListener('error', () => {
    stopped();
    showToast(ro.player.error);
  });
  element = audio;
  return audio;
}

function load(trackId: number, url: string, durationS: number) {
  const audio = audioElement();
  if (usePlayer.getState().trackId === trackId) return audio;
  audio.pause();
  audio.src = url;
  usePlayer.setState({ trackId, playing: false, positionS: 0, durationS });
  return audio;
}

function start(audio: HTMLAudioElement) {
  void context?.resume();
  audio.play().catch(() => {
    /* eroarea de redare ajunge prin evenimentul `error` */
  });
}

export const player = {
  /** Play/pauză pentru piesa dată; o piesă nouă o înlocuiește pe cea care cântă. */
  toggle(trackId: number, url: string, durationS: number) {
    const audio = load(trackId, url, durationS);
    if (usePlayer.getState().playing) audio.pause();
    else start(audio);
  },

  /** Sare la `seconds` în piesa dată și cântă de acolo. */
  playFrom(trackId: number, url: string, durationS: number, seconds: number) {
    const audio = load(trackId, url, durationS);
    audio.currentTime = seconds;
    usePlayer.setState({ positionS: seconds });
    start(audio);
  },

  pause() {
    element?.pause();
  },
};
