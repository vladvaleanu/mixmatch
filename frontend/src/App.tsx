import { Navigate, Route, Routes } from 'react-router-dom';

import { ExportsScreen } from './features/exports/ExportsScreen';
import { ImportButton } from './features/library/ImportButton';
import { LibraryScreen } from './features/library/LibraryScreen';
import { LibrarySearch } from './features/library/LibrarySearch';
import { MixBuilderScreen } from './features/mix-builder/MixBuilderScreen';
import { MixesScreen } from './features/mix-builder/MixesScreen';
import { TransitionScreen } from './features/transition/TransitionScreen';
import { Toast } from './ui/Toast';
import { TopBar } from './ui/TopBar';

export function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopBar search={<LibrarySearch />} actions={<ImportButton />} />
      <main style={{ flex: 1, display: 'flex' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/biblioteca" replace />} />
          <Route path="/biblioteca" element={<LibraryScreen />} />
          <Route path="/mixuri" element={<MixesScreen />} />
          <Route path="/mixuri/:mixId" element={<MixBuilderScreen />} />
          <Route path="/mixuri/:mixId/tranzitii/:position" element={<TransitionScreen />} />
          <Route path="/exporturi" element={<ExportsScreen />} />
          <Route path="*" element={<Navigate to="/biblioteca" replace />} />
        </Routes>
      </main>
      <Toast />
    </div>
  );
}
