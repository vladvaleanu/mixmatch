import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import { useActiveJobs } from '../../api/jobs';
import { tracksKey } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, radius, space } from '../../theme/tokens';
import { ProgressBar } from '../../ui/ProgressBar';

/** Progresul analizei din fundal; reîncarcă tabelul ca rezultatele să apară pe măsură ce vin. */
export function AnalysisBanner() {
  const queryClient = useQueryClient();
  const analysis = useActiveJobs().data?.find((job) => job.kind === 'analysis');
  const progress = analysis?.progress;

  // Și la final (progress devine undefined), ca ultimele piese analizate să apară.
  useEffect(() => {
    void queryClient.invalidateQueries({ queryKey: tracksKey });
  }, [progress, queryClient]);

  if (!analysis) return null;
  return (
    <div
      role="status"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: space[8],
        padding: `${space[14]}px ${space[16]}px`,
        borderRadius: radius.control,
        background: color.surface2,
        color: color.textSoft,
      }}
    >
      <span>
        {ro.analysis.running} {Math.round(analysis.progress * 100)}%
      </span>
      <ProgressBar value={analysis.progress} label={ro.analysis.progressLabel} />
    </div>
  );
}
