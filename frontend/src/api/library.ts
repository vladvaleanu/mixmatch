import { useMutation } from '@tanstack/react-query';

import { http, unwrap } from './client';

export function useAddFolder() {
  return useMutation({
    mutationFn: (path: string) => unwrap(http.POST('/api/library/folders', { body: { path } })),
  });
}

/** Trimite fișierele trase în Bibliotecă; serverul le copiază și pornește scanarea. */
export function useUploadTracks() {
  return useMutation({
    mutationFn: (files: File[]) =>
      unwrap(
        http.POST('/api/library/upload', {
          body: { files: [] },
          bodySerializer: () => {
            const form = new FormData();
            for (const file of files) form.append('files', file, file.name);
            return form;
          },
        }),
      ),
  });
}
