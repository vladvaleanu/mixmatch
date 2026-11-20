import { useState } from 'react';

import { useExportMix } from '../../api/exports';
import { useJob } from '../../api/jobs';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { ProgressBar } from '../../ui/ProgressBar';

type Format = 'wav' | 'mp3';

/** Alegi formatul, pornești randarea și vezi unde s-a salvat fișierul. */
export function ExportDialog({ mixId, onClose }: { mixId: number; onClose: () => void }) {
  const [format, setFormat] = useState<Format>('wav');
  const exportMix = useExportMix(mixId);
  const job = useJob(exportMix.data?.job_id ?? null).data;
  const e = ro.exportMix;

  return (
    <Dialog title={e.title} onClose={onClose}>
      {!exportMix.data ? (
        <>
          <p style={{ margin: 0, color: color.textSoft, lineHeight: 1.5 }}>{e.intro}</p>
          <fieldset
            style={{
              border: 0,
              margin: 0,
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: space[8],
            }}
          >
            <legend
              style={{ color: color.textMuted, fontSize: fontSize.meta, marginBottom: space[6] }}
            >
              {e.format}
            </legend>
            {(['wav', 'mp3'] as const).map((value) => (
              <label
                key={value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: space[10],
                  padding: `${space[10]}px ${space[12]}px`,
                  borderRadius: radius.control,
                  background: format === value ? color.accentSoftBg : color.surface2,
                  border: `1px solid ${format === value ? color.accent : color.border}`,
                  cursor: 'pointer',
                }}
              >
                <input
                  type="radio"
                  name="format"
                  value={value}
                  checked={format === value}
                  onChange={() => setFormat(value)}
                  style={{ width: 18, height: 18, accentColor: color.accent, margin: 0 }}
                />
                {e[value]}
              </label>
            ))}
          </fieldset>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: space[8] }}>
            <Button onClick={onClose}>{ro.common.cancel}</Button>
            <Button
              variant="primary"
              disabled={exportMix.isPending}
              onClick={() => exportMix.mutate(format)}
            >
              {e.start}
            </Button>
          </div>
        </>
      ) : (
        <>
          {job?.status === 'done' ? (
            <>
              <p style={{ margin: 0 }}>{e.done}</p>
              <code
                style={{
                  padding: space[10],
                  borderRadius: radius.buttonSm,
                  background: color.surface2,
                  color: color.textSoft,
                  fontSize: fontSize.meta,
                  overflowWrap: 'anywhere',
                }}
              >
                {exportMix.data.path}
              </code>
            </>
          ) : job?.status === 'failed' ? (
            <p style={{ margin: 0, color: color.warnSoftText }}>
              {e.failed} {job.error}
            </p>
          ) : (
            <>
              <span style={{ color: color.textSoft }}>
                {e.rendering} {Math.round((job?.progress ?? 0) * 100)}%
              </span>
              <ProgressBar value={job?.progress ?? 0} label={e.progressLabel} />
            </>
          )}
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant={job?.status === 'done' ? 'primary' : 'secondary'} onClick={onClose}>
              {ro.common.close}
            </Button>
          </div>
        </>
      )}
    </Dialog>
  );
}
