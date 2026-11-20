import { useEffect } from 'react';

import { ro } from '../i18n/ro';
import { color, radius, space, zIndex } from '../theme/tokens';
import { useToastStore } from './toastStore';

const HIDE_AFTER_MS = 6000;

/** Toast-ul global pentru erori. Apare jos, în centru, și dispare singur. */
export function Toast() {
  const { message, dismiss } = useToastStore();

  useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(dismiss, HIDE_AFTER_MS);
    return () => window.clearTimeout(timer);
  }, [message, dismiss]);

  if (!message) return null;
  return (
    <div
      role="alert"
      style={{
        position: 'fixed',
        left: '50%',
        bottom: space[24],
        transform: 'translateX(-50%)',
        zIndex: zIndex.toast,
        maxWidth: `min(560px, calc(100vw - ${2 * space[16]}px))`,
        display: 'flex',
        alignItems: 'center',
        gap: space[12],
        padding: `${space[12]}px ${space[16]}px`,
        borderRadius: radius.control,
        background: color.warnSoftBg,
        color: color.warnSoftText,
        border: `1px solid ${color.borderStrong}`,
      }}
    >
      <span style={{ flex: 1 }}>{message}</span>
      <button
        type="button"
        onClick={dismiss}
        aria-label={ro.common.close}
        style={{
          border: 0,
          background: 'transparent',
          color: 'inherit',
          cursor: 'pointer',
          font: 'inherit',
          padding: space[4],
          display: 'flex',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M6 6l12 12M18 6L6 18"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </button>
    </div>
  );
}
