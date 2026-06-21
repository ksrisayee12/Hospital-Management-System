import React, { useState } from 'react';
import { AppShell } from './components/layout';
import { ToastProvider } from './components/primitives';
import CommandCenterPage from './pages/CommandCenterPage';
import InvestigationsPage from './pages/InvestigationsPage';
import TrustRiskPage from './pages/TrustRiskPage';
import GovernanceLedgerPage from './pages/GovernanceLedgerPage';
import NetworkAnalyticsPage from './pages/NetworkAnalyticsPage';
import DevLogin from './components/DevLogin';
import './styles/globals.css';

const PAGES = {
  'command-center':    CommandCenterPage,
  investigations:      InvestigationsPage,
  'trust-risk':        TrustRiskPage,
  'governance-ledger': GovernanceLedgerPage,
  'network-analytics': NetworkAnalyticsPage,
};

export default function App() {
  const [active, setActive] = useState('command-center');
  const ActivePage = PAGES[active] || CommandCenterPage;

  return (
    <ToastProvider>
      <DevLogin />
      <AppShell active={active} onNavigate={setActive}>
        <ActivePage />
      </AppShell>
    </ToastProvider>
  );
}
