import { describe, expect, it } from 'vitest';

import { droppedAudioFiles, isAudio } from './dropFiles';

function fileEntry(name: string) {
  return {
    isFile: true,
    isDirectory: false,
    name,
    file: (ok: (f: File) => void) => ok(new File(['x'], name)),
  };
}

function dirEntry(children: unknown[]) {
  return {
    isFile: false,
    isDirectory: true,
    createReader: () => {
      let done = false;
      // Ca în browser: un lot cu tot, apoi un lot gol.
      return {
        readEntries: (ok: (e: unknown[]) => void) => ok(done ? [] : ((done = true), children)),
      };
    },
  };
}

describe('drag & drop', () => {
  it('parcurge folderele și păstrează doar audio', async () => {
    const tree = dirEntry([
      fileEntry('a.mp3'),
      fileEntry('cover.jpg'),
      dirEntry([fileEntry('B.FLAC'), fileEntry('._b.flac'), fileEntry('notes.txt')]),
    ]);
    const data = {
      items: [{ webkitGetAsEntry: () => tree }],
      files: [],
    } as unknown as DataTransfer;
    const files = await droppedAudioFiles(data);
    expect(files.map((f) => f.name).sort()).toEqual(['B.FLAC', 'a.mp3']);
  });

  it('recunoaște formatele acceptate', () => {
    expect(['x.mp3', 'x.wav', 'x.aiff', 'x.aif', 'x.m4a', 'x.flac'].every(isAudio)).toBe(true);
    expect(['x.ogg', 'x.txt', '.x.mp3'].some(isAudio)).toBe(false);
  });
});
