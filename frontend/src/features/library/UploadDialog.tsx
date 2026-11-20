import { ro } from '../../i18n/ro';
import { color, fontSize } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { ScanProgress } from './ScanProgress';

type Props = {
  count: number; // câte fișiere audio s-au tras
  result: { job_id: number; skipped: string[] } | undefined;
  pending: boolean;
  onClose: () => void;
};

/** Importul prin drag & drop: copierea, apoi scanarea folderului administrat. */
export function UploadDialog({ count, result, pending, onClose }: Props) {
  const u = ro.upload;
  return (
    <Dialog title={u.title} onClose={onClose}>
      {count === 0 ? (
        <>
          <p style={{ margin: 0, color: color.textSoft }}>{u.none}</p>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={onClose}>{ro.common.close}</Button>
          </div>
        </>
      ) : result ? (
        <ScanProgress
          jobId={result.job_id}
          onClose={onClose}
          note={
            result.skipped.length > 0 && (
              <p style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta }}>
                {u.skipped(result.skipped)}
              </p>
            )
          }
        />
      ) : (
        <>
          <p style={{ margin: 0, color: color.textSoft }}>{pending ? u.copying(count) : ''}</p>
          <p style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta }}>{u.where}</p>
        </>
      )}
    </Dialog>
  );
}
