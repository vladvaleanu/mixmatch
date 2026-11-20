import type { CSSProperties, ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

import { useHealth } from '../api/health';
import { ro } from '../i18n/ro';
import { color, font, fontSize, radius, space } from '../theme/tokens';

const navItems = [
  { to: '/biblioteca', label: ro.nav.library },
  { to: '/mixuri', label: ro.nav.mixes },
  { to: '/exporturi', label: ro.nav.exports },
] as const;

const styles = {
  header: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: `${space[16]}px ${space[28]}px`,
    padding: `${space[16]}px ${space[28]}px`,
    borderBottom: `1px solid ${color.border}`,
  },
  logo: { display: 'flex', alignItems: 'center', gap: space[10] },
  logoText: {
    fontFamily: font.display,
    fontSize: fontSize.logo,
    fontWeight: 600,
    letterSpacing: '-0.01em',
  },
  nav: { display: 'flex', gap: space[4] },
  status: {
    marginLeft: 'auto',
    display: 'flex',
    alignItems: 'center',
    gap: space[8],
    color: color.textMuted,
    fontSize: fontSize.meta,
  },
} satisfies Record<string, CSSProperties>;

function navLinkStyle({ isActive }: { isActive: boolean }): CSSProperties {
  return {
    padding: `${space[10]}px ${space[16]}px`,
    borderRadius: radius.round,
    background: isActive ? color.surface3 : 'transparent',
    color: isActive ? color.text : color.textMuted,
    textDecoration: 'none',
    fontWeight: 500,
  };
}

function HealthStatus() {
  const health = useHealth();
  const state = health.isPending ? 'checking' : health.isSuccess ? 'ok' : 'down';
  const dotColor = { checking: color.borderDashed, ok: color.accent, down: color.warn }[state];

  return (
    <div role="status" style={styles.status}>
      <span
        aria-hidden="true"
        style={{ width: 8, height: 8, borderRadius: radius.round, background: dotColor }}
      />
      {ro.health[state]}
    </div>
  );
}

type Props = { search?: ReactNode; actions?: ReactNode };

export function TopBar({ search, actions }: Props) {
  return (
    <header style={styles.header}>
      <div style={styles.logo}>
        <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
          <circle cx="14" cy="14" r="12" fill="none" stroke={color.accent} strokeWidth="2" />
          <circle cx="14" cy="14" r="3" fill={color.accent} />
        </svg>
        <span style={styles.logoText}>{ro.appName}</span>
      </div>
      <nav aria-label={ro.nav.label} style={styles.nav}>
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} style={navLinkStyle}>
            {item.label}
          </NavLink>
        ))}
      </nav>
      {search}
      <HealthStatus />
      {actions}
    </header>
  );
}
