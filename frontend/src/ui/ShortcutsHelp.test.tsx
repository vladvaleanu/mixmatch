import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ro } from '../i18n/ro';
import { ShortcutsHelp } from './ShortcutsHelp';

afterEach(cleanup);

describe('scurtături globale', () => {
  it('„?” deschide lista, „/” mută focusul în căutare', () => {
    render(
      <>
        <input id="library-search" aria-label="caută" />
        <ShortcutsHelp />
      </>,
    );
    fireEvent.keyDown(document.body, { key: '/' });
    expect(document.activeElement).toBe(screen.getByLabelText('caută'));

    (document.activeElement as HTMLElement).blur();
    fireEvent.keyDown(document.body, { key: '?' });
    expect(screen.getByRole('dialog', { name: ro.shortcuts.title })).toBeTruthy();
    expect(screen.getByText(ro.shortcuts.play)).toBeTruthy();
  });

  it('nu reacționează cât scrii', () => {
    render(
      <>
        <input aria-label="câmp" />
        <ShortcutsHelp />
      </>,
    );
    fireEvent.keyDown(screen.getByLabelText('câmp'), { key: '?' });
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});
