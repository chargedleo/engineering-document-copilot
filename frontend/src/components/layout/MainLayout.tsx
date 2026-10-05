import React, { useState } from 'react';
import { Sidebar, ActiveTab } from './Sidebar';
import { Header } from './Header';

interface MainLayoutProps {
  children: (activeTab: ActiveTab) => React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat');

  const getTitle = () => {
    switch (activeTab) {
      case 'chat':
        return 'Engineering Copilot Workspace';
      case 'documents':
        return 'Document Intelligence & Ingestion';
      case 'cad':
        return 'CAD Knowledge & Assemblies';
      case 'architecture':
        return 'System Architecture & Capabilities';
      default:
        return 'Engineering Document Copilot';
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="main-content">
        <Header title={getTitle()} />
        <main className="content-body">
          {children(activeTab)}
        </main>
      </div>
    </div>
  );
};
