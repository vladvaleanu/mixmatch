// Singurul loc din aplicație care atinge Web Audio și elementul <audio>.
// Un singur player pentru toată aplicația: o piesă nouă o oprește pe cea veche.
import { create } from 'zustand';

import { ro } from '../i18n/ro';
import { showToast } from '../ui/toastStore';
import { clipRanges, type ClipRange, type Plan } from './plan';
import { previewLength, scheduleTransition } from './transition';

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

function audioContext(): AudioContext {
  context ??= new AudioContext();
  return context;
}

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
    const ctx = audioContext();
    ctx.createMediaElementSource(audio).connect(ctx.destination);
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
  transitionPreview.stop(); // un singur lucru se aude odată
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

// ——— Previzualizarea unei tranziții ———

export type PreviewState = {
  key: string | null; // ce tranziție (ex. „7/3”)
  status: 'idle' | 'loading' | 'playing';
  /** Momentul curent în timpul tranziției (0 = începutul ei), cât cântă. */
  t: number | null;
};

export const usePreview = create<PreviewState>(() => ({ key: null, status: 'idle', t: null }));

/** Încarcă o bucată de audio (WAV) dintr-o piesă: e dat de cine cheamă, prin `api/`. */
export type ClipLoader = (deck: 'a' | 'b', range: ClipRange) => Promise<ArrayBuffer>;

let stopPreview: (() => void) | null = null;
let previewFrame = 0;
let previewRun = 0;

export const transitionPreview = {
  /** Cântă fereastra tranziției, exclusiv din plan și din bucățile încărcate. */
  async play(key: string, plan: Plan, load: ClipLoader) {
    transitionPreview.stop();
    element?.pause();
    const run = ++previewRun;
    usePreview.setState({ key, status: 'loading', t: null });
    const ctx = audioContext();
    void ctx.resume();
    try {
      const ranges = clipRanges(plan);
      const [a, b] = await Promise.all([
        load('a', ranges.a).then((data) => ctx.decodeAudioData(data)),
        load('b', ranges.b).then((data) => ctx.decodeAudioData(data)),
      ]);
      if (run !== previewRun) return; // între timp s-a cerut altceva
      const startAt = ctx.currentTime + 0.1;
      const stop = scheduleTransition(ctx, plan, { a, b }, ctx.destination, startAt);
      const length = previewLength(plan);
      stopPreview = stop;
      usePreview.setState({ status: 'playing' });
      const tick = () => {
        const elapsed = ctx.currentTime - startAt;
        if (elapsed >= length) {
          transitionPreview.stop();
          return;
        }
        usePreview.setState({ t: plan.preview_start_s + Math.max(0, elapsed) });
        previewFrame = requestAnimationFrame(tick);
      };
      previewFrame = requestAnimationFrame(tick);
    } catch {
      if (run === previewRun) {
        usePreview.setState({ key: null, status: 'idle', t: null });
        showToast(ro.player.previewError);
      }
    }
  },

  stop() {
    previewRun++;
    cancelAnimationFrame(previewFrame);
    stopPreview?.();
    stopPreview = null;
    if (usePreview.getState().status !== 'idle') {
      usePreview.setState({ key: null, status: 'idle', t: null });
    }
  },
};
