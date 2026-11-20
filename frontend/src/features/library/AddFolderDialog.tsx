import { useState, type FormEvent } from 'react';

import { useAddFolder } from '../../api/library';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, size, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { ScanProgress } from './ScanProgress';

type Props = { onClose: () => void };

export function AddFolderDialog({ onClose }: Props) {
  const [path, setPath] = useState('');
  const addFolder = useAddFolder();
  const jobId = addFolder.data?.job_id ?? null;

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
            <Button variant="primary" type="submit" disabled={addFolder.isPending || !path.trim()}>
              {ro.addFolder.submit}
            </Button>
          </div>
        </form>
      ) : (
        <ScanProgress jobId={jobId} onClose={onClose} />
      )}
    </Dialog>
  );
}
