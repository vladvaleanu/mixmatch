// Fișierele dintr-un drag & drop, inclusiv cele din folderele trase (recursiv).

const AUDIO = ['.mp3', '.flac', '.wav', '.aif', '.aiff', '.m4a'];

/** Doar fișierele audio: nu are rost să trimitem coperți sau documente la server. */
export function isAudio(name: string): boolean {
  const lower = name.toLowerCase();
  return AUDIO.some((ext) => lower.endsWith(ext)) && !name.startsWith('.');
}

async function readAll(dir: FileSystemDirectoryEntry): Promise<FileSystemEntry[]> {
  const reader = dir.createReader();
  const out: FileSystemEntry[] = [];
  // readEntries întoarce câte un lot; un lot gol înseamnă sfârșitul.
  for (;;) {
    const batch = await new Promise<FileSystemEntry[]>((resolve, reject) =>
      reader.readEntries(resolve, reject),
    );
    if (batch.length === 0) return out;
    out.push(...batch);
  }
}

async function collect(entry: FileSystemEntry): Promise<File[]> {
  if (entry.isFile) {
    const file = await new Promise<File>((resolve, reject) =>
      (entry as FileSystemFileEntry).file(resolve, reject),
    );
    return [file];
  }
  if (entry.isDirectory) {
    const children = await readAll(entry as FileSystemDirectoryEntry);
    return (await Promise.all(children.map(collect))).flat();
  }
  return [];
}

export async function droppedAudioFiles(data: DataTransfer): Promise<File[]> {
  const entries = Array.from(data.items)
    .map((item) => item.webkitGetAsEntry?.())
    .filter((entry): entry is FileSystemEntry => Boolean(entry));
  const files = entries.length
    ? (await Promise.all(entries.map(collect))).flat()
    : Array.from(data.files);
  return files.filter((file) => isAudio(file.name));
}
