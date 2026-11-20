import { Navigate, Route, Routes } from 'react-router-dom';

import { ExportsScreen } from './features/exports/ExportsScreen';
import { LibraryScreen } from './features/library/LibraryScreen';
import { MixesScreen } from './features/mix-builder/MixesScreen';
import { space } from './theme/tokens';
import { TopBar } from './ui/TopBar';

export function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopBar />
      <main style={{ flex: 1, padding: `${space[32]}px ${space[28]}px` }}>
        <Routes>
          <Route path="/" element={<Navigate to="/biblioteca" replace />} />
          <Route path="/biblioteca" element={<LibraryScreen />} />
          <Route path="/mixuri" element={<MixesScreen />} />
          <Route path="/exporturi" element={<ExportsScreen />} />
          <Route path="*" element={<Navigate to="/biblioteca" replace />} />
        </Routes>
      </main>
    </div>
  );
}
