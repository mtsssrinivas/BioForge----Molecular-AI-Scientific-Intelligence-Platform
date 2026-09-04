import React, { useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { MoleculesPage } from './pages/MoleculesPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { PredictionPage } from './pages/PredictionPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { ModelsPage } from './pages/ModelsPage';
import { LiteraturePage } from './pages/LiteraturePage';
import { RAGPage } from './pages/RAGPage';
import { JobsPage } from './pages/JobsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardPage onNavigate={setCurrentTab} />;
      case 'molecules':
        return <MoleculesPage />;
      case 'datasets':
        return <DatasetsPage />;
      case 'predictions':
        return <PredictionPage />;
      case 'experiments':
        return <ExperimentsPage />;
      case 'models':
        return <ModelsPage />;
      case 'literature':
        return <LiteraturePage />;
      case 'rag':
        return <RAGPage />;
      case 'jobs':
        return <JobsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage onNavigate={setCurrentTab} />;
    }
  };

  return (
    <AppShell currentTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </AppShell>
  );
}

export default App;
