import React from 'react';
import { MainLayout } from './components/layout/MainLayout';
import { ChatWindow } from './components/chat/ChatWindow';
import { DocumentList } from './components/documents/DocumentList';
import { CadViewerPlaceholder } from './components/cad/CadViewerPlaceholder';
import { ArchitectureView } from './components/architecture/ArchitectureView';

export const App: React.FC = () => {
  return (
    <MainLayout>
      {(activeTab) => {
        switch (activeTab) {
          case 'chat':
            return <ChatWindow />;
          case 'documents':
            return <DocumentList />;
          case 'cad':
            return <CadViewerPlaceholder />;
          case 'architecture':
            return <ArchitectureView />;
          default:
            return <ChatWindow />;
        }
      }}
    </MainLayout>
  );
};

export default App;
