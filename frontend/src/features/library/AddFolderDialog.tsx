import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type FormEvent } from 'react';

import { activeJobsKey, useJob } from '../../api/jobs';
import { useAddFolder } from '../../api/library';
import { tracksKey, useTracks } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, size, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { ProgressBar } from '../../ui/ProgressBar';

type Props = { onClose: () => void };

export function AddFolderDialog({ onClose }: Props) {
  const [path, setPath] = useState('');
  const addFolder = useAddFolder();
  const jobId = addFolder.data?.job_id ?? null;
  const job = useJob(jobId).data;
  const tracks = useTracks();
  const queryClient = useQueryClient();

  const finished = job?.status === 'done' || job?.status === 'failed';
  const busy = addFolder.isPending || (jobId !== null && !finished);

  // Piesele apar în tabel pe măsură ce scanarea le salvează, apoi încă o dată la final.
  useEffect(() => {
    if (job) void queryClient.invalidateQueries({ queryKey: tracksKey });
  }, [job, queryClient]);

  // După scanare pornește analiza; bannerul din Bibliotecă o află din joburile active.
  useEffect(() => {
    if (finished) void queryClient.invalidateQueries({ queryKey: activeJobsKey });
  }, [finished, queryClient]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (path.trim()) addFolder.mutate(path.trim());
  };

  return (
    <Dialog title={ro.addFolder.title} onClose={onClose}>
      {jobId === null ? (
        <form
          onSubmit={submit}
          style={{ display: 'flex', flexDirection: 'column', gap: space[16] }}
        >
          <p style={{ margin: 0, color: color.textSoft }}>{ro.addFolder.intro}</p>
          <label style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
            <span style={{ color: color.textSoft }}>{ro.addFolder.pathLabel}</span>
            <input
              value={path}
              onChange={(event) => setPath(event.target.value)}
              placeholder={ro.addFolder.pathPlaceholder}
              spellCheck={false}
              autoComplete="off"
              style={{
                height: size.touch,
                padding: `0 ${space[14]}px`,
                borderRadius: radius.control,
                border: `1px solid ${color.borderStrong}`,
                background: color.surface2,
                color: color.text,
                font: 'inherit',
              }}
            />
          </label>
          <p style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta }}>
            {ro.addFolder.hint}
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: space[8] }}>
            <Button onClick={onClose}>{ro.common.cancel}</Button>
            <Button variant="primary" type="submit" disabled={busy || !path.trim()}>
              {ro.addFolder.submit}
            </Button>
          </div>
        </form>
      ) : (
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
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant={finished ? 'primary' : 'secondary'} onClick={onClose}>
              {ro.common.close}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
