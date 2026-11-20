import { ro } from '../../i18n/ro';
import { space } from '../../theme/tokens';
import { ScreenHeader } from '../../ui/ScreenHeader';

export function MixesScreen() {
  return (
    <div style={{ padding: space[28] }}>
      <ScreenHeader {...ro.screens.mixes} />
    </div>
  );
}
