import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ro } from '../i18n/ro';
import { TransitionTag } from './TransitionTag';

afterEach(cleanup);

describe('TransitionTag', () => {
  it.each([
    ['smooth', 'circle'],
    ['good', 'rect'],
    ['caution', 'path'],
  ] as const)('%s are text și formă proprie (%s)', (label, shape) => {
    const { container } = render(<TransitionTag label={label} />);
    expect(screen.getByText(ro.transition[label])).toBeTruthy();
    expect(container.querySelector(`svg ${shape}`)).toBeTruthy();
  });
});
