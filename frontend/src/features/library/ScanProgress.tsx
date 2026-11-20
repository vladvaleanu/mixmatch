import { useQueryClient } from '@tanstack/react-query';
import { useEffect, type ReactNode } from 'react';

import { activeJobsKey, useJob } from '../../api/jobs';
import { tracksKey, useTracks } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, fontSize, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { ProgressBar } from '../../ui/ProgressBar';

/** Progresul unei scanări (după „Adaugă folder” sau după un upload), apoi rezultatul. */
export function ScanProgress({
  jobId,
  note,
  onClose,
}: {
  jobId: number;
  note?: ReactNode; // ex. fișierele sărite la upload
  onClose: () => void;
}) {
  const job = useJob(jobId).data;
  const tracks = useTracks();
  const queryClient = useQueryClient();
  const finished = job?.status === 'done' || job?.status === 'failed';

  // Piesele apar în tabel pe măsură ce scanarea le salvează, apoi încă o dată la final.
  useEffect(() => {
    if (job) void queryClient.invalidateQueries({ queryKey: tracksKey });
  }, [job, queryClient]);

  // După scanare pornește analiza; bannerul din Bibliotecă o află din joburile active.
  useEffect(() => {
    if (finished) void queryClient.invalidateQueries({ queryKey: activeJobsKey });
  }, [finished, queryClient]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[16] }}>
      {job?.status === 'failed' ? (
        <p style={{ margin: 0, color: color.warnSoftText }}>
          {ro.addFolder.failed} {job.error}
        </p>
      ) : job?.status === 'done' ? (
        <>
          <p style={{ margin: 0 }}>{ro.addFolder.done(tracks.data?.length ?? 0)}</p>
          <p style={{ margin: 0, color: color.textSoft }}>{ro.addFolder.analysisContinues}</p>
          <p style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta }}>
            {ro.addFolder.shortSkipped}
          </p>
        </>
      ) : (
        <>
          <span style={{ color: color.textSoft }}>
            {ro.addFolder.scanning} {Math.round((job?.progress ?? 0) * 100)}%
          </span>
          <ProgressBar value={job?.progress ?? 0} label={ro.addFolder.progressLabel} />
        </>
      )}
      {note}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant={finished ? 'primary' : 'secondary'} onClick={onClose}>
          {ro.common.close}
        </Button>
      </div>
    </div>
  );
}
