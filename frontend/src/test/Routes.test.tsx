import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotFoundPage } from '../pages/NotFoundPage';
import { SettingsPage } from '../pages/SettingsPage';

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe('Routing and Fallbacks', () => {
  it('renders NotFoundPage on invalid route', () => {
    renderWithClient(
      <MemoryRouter initialEntries={['/unknown-path']}>
        <Routes>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    expect(screen.getByText(/The navigation route you accessed is not recognized/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /return to overview/i })).toBeInTheDocument();
  });

  it('renders SettingsPage on /settings route', () => {
    renderWithClient(
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText(/Backend Ingestion Binding/)).toBeInTheDocument();
  });
});
