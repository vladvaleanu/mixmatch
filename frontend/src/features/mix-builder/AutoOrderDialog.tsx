import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, fontSize, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { TransitionTag } from '../../ui/TransitionTag';

type Proposal = Schemas['AutoOrderOut'];

const count = (labels: Proposal['labels'], label: 'smooth' | 'caution') =>
  labels.filter((l) => l === label).length;

/** Previzualizarea ordonării automate: o accepți (se salvează) sau o refuzi. */
export function AutoOrderDialog({
  proposal,
  onAccept,
  onClose,
}: {
  proposal: Proposal;
  onAccept: () => void;
  onClose: () => void;
}) {
  const a = ro.autoOrder;
  return (
    <Dialog title={a.title} onClose={onClose}>
      {!proposal.changed ? (
        <p style={{ margin: 0, color: color.textSoft }}>{a.unchanged}</p>
      ) : (
        <>
          <p style={{ margin: 0, color: color.textSoft, lineHeight: 1.5 }}>{a.intro}</p>
          <div
            style={{ display: 'flex', flexWrap: 'wrap', gap: space[12], fontSize: fontSize.meta }}
          >
            <span style={{ color: color.warnSoftText }}>
              {a.caution(
                count(proposal.current_labels, 'caution'),
                count(proposal.labels, 'caution'),
              )}
            </span>
            <span style={{ color: color.accentSoftText }}>
              {a.smooth(count(proposal.current_labels, 'smooth'), count(proposal.labels, 'smooth'))}
            </span>
          </div>
          <ol
            style={{
              margin: 0,
              padding: 0,
              listStyle: 'none',
              maxHeight: '50vh',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: space[6],
            }}
          >
            {proposal.tracks.map((track, i) => {
              const label = i > 0 ? proposal.labels[i - 1] : null;
              return (
                <li
                  key={track.id}
                  style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}
                >
                  {label && (
                    <span style={{ paddingLeft: space[28] }}>
                      <TransitionTag label={label} />
                    </span>
                  )}
                  <span style={{ display: 'flex', gap: space[10], alignItems: 'baseline' }}>
                    <span
                      style={{
                        width: 18,
                        color: color.textMuted,
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {i + 1}
                    </span>
                    <span>
                      <span style={{ fontWeight: 500 }}>{track.title}</span>
                      <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                        {' '}
                        · {track.artist ?? ro.library.unknownArtist}
                      </span>
                    </span>
                  </span>
                </li>
              );
            })}
          </ol>
        </>
      )}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: space[8] }}>
        <Button onClick={onClose}>{proposal.changed ? a.reject : ro.common.close}</Button>
        {proposal.changed && (
          <Button variant="primary" onClick={onAccept}>
            {a.accept}
          </Button>
        )}
      </div>
    </Dialog>
  );
}
