import { Link } from 'react-router-dom';

import { exportFileUrl, useExports } from '../../api/exports';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, space } from '../../theme/tokens';
import { formatMinutes } from '../../ui/format';
import { EmptyState } from '../../ui/EmptyState';
import { ProgressBar } from '../../ui/ProgressBar';
import { ScreenHeader } from '../../ui/ScreenHeader';

const dateFormat = new Intl.DateTimeFormat('ro-RO', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});

const KINDS = ['audio', 'tracklist', 'cue'] as const;

export function ExportsScreen() {
  const exports = useExports();
  const e = ro.screens.exports;

  return (
    <div
      style={{
        flex: 1,
        padding: space[28],
        display: 'flex',
        flexDirection: 'column',
        gap: space[24],
        maxWidth: 1000,
      }}
    >
      <ScreenHeader title={e.title} subtitle={e.subtitle} />
      {exports.isPending ? (
        <p style={{ margin: 0, color: color.textMuted }}>{e.loading}</p>
      ) : exports.data?.length === 0 ? (
        <EmptyState
          title={ro.empty.exportsTitle}
          text={ro.empty.exportsText}
          action={
            <Link to="/mixuri" style={{ color: color.accent }}>
              {ro.empty.exportsAction}
            </Link>
          }
        />
      ) : (
        <ul
          style={{
            listStyle: 'none',
            margin: 0,
            padding: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: space[12],
          }}
        >
          {exports.data?.map((item) => {
            const status = item.job?.status ?? 'done';
            const busy = status === 'queued' || status === 'running';
            return (
              <li
                key={item.id}
                style={{
                  padding: space[18],
                  borderRadius: radius.card,
                  background: color.surface,
                  border: `1px solid ${color.border}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: space[10],
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'baseline',
                    justifyContent: 'space-between',
                    gap: space[8],
                  }}
                >
                  <span style={{ fontFamily: font.display, fontSize: 20, fontWeight: 600 }}>
                    {item.mix_name}
                  </span>
                  <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                    {e.meta(
                      item.format,
                      dateFormat.format(new Date(item.created_at)),
                      item.duration_s !== null ? formatMinutes(item.duration_s) : null,
                    )}
                    {item.mix_id === null && ` · ${e.deletedMix}`}
                  </span>
                </div>

                {busy ? (
                  <>
                    <span style={{ color: color.textSoft }}>
                      {status === 'queued'
                        ? e.queued
                        : e.rendering(Math.round((item.job?.progress ?? 0) * 100))}
                    </span>
                    <ProgressBar
                      value={item.job?.progress ?? 0}
                      label={e.rendering(Math.round((item.job?.progress ?? 0) * 100))}
                    />
                  </>
                ) : status === 'failed' ? (
                  <p style={{ margin: 0, color: color.warnSoftText }}>
                    {e.failed} {item.job?.error}
                  </p>
                ) : (
                  <>
                    <code
                      style={{
                        color: color.textMuted,
                        fontSize: fontSize.meta,
                        overflowWrap: 'anywhere',
                      }}
                    >
                      {item.path}
                    </code>
                    {item.files.includes('audio') ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: space[8] }}>
                        {KINDS.filter((kind) => item.files.includes(kind)).map((kind) => (
                          <a
                            key={kind}
                            href={exportFileUrl(item.id, kind)}
                            download
                            style={{
                              padding: `${space[10]}px ${space[14]}px`,
                              borderRadius: radius.buttonSm,
                              background: kind === 'audio' ? color.accent : color.surface2,
                              color: kind === 'audio' ? color.accentText : color.text,
                              border: kind === 'audio' ? 0 : `1px solid ${color.borderStrong}`,
                              fontWeight: kind === 'audio' ? 600 : 500,
                              textDecoration: 'none',
                            }}
                          >
                            {e.download[kind]}
                          </a>
                        ))}
                        {item.mix_id !== null && (
                          <Link
                            to={`/mixuri/${item.mix_id}`}
                            style={{
                              alignSelf: 'center',
                              color: color.textMuted,
                              fontSize: fontSize.meta,
                            }}
                          >
                            {e.openMix}
                          </Link>
                        )}
                      </div>
                    ) : (
                      <p style={{ margin: 0, color: color.textMuted }}>{e.missing}</p>
                    )}
                  </>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
