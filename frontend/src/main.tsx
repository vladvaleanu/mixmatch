import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/space-grotesk/600.css';

import { QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { createQueryClient } from './api/queryClient';
import { App } from './App';
import { GlobalStyle } from './theme/GlobalStyle';

const queryClient = createQueryClient();

const root = document.getElementById('root');
if (!root) throw new Error('#root lipsește din index.html');

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <GlobalStyle />
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
