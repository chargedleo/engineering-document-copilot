import React from 'react';
import { MainLayout } from './components/layout/MainLayout';
import { ChatWindow } from './components/chat/ChatWindow';
import { DocumentList } from './components/documents/DocumentList';
import { CadViewerPlaceholder } from './components/cad/CadViewerPlaceholder';
import { Card } from './components/common/Card';
import { Badge } from './components/common/Badge';

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
            return (
              <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <Card title="System Architecture & Stack" subtitle="Engineering Document Intelligence & CAD Knowledge Copilot">
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: '6px' }}>
                      <Badge variant="info">Backend</Badge>
                      <h4 style={{ margin: '0.5rem 0' }}>FastAPI & SQLAlchemy</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        Async REST API with Pydantic validation, connection pooling, and structured logging.
                      </p>
                    </div>

                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: '6px' }}>
                      <Badge variant="info">Frontend</Badge>
                      <h4 style={{ margin: '0.5rem 0' }}>React 18 + TypeScript + Vite</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        Clean component architecture, typed API contracts, and responsive layout.
                      </p>
                    </div>

                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: '6px' }}>
                      <Badge variant="warning">AI Engine (Staged)</Badge>
                      <h4 style={{ margin: '0.5rem 0' }}>LangGraph & Azure OpenAI</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        State machine workflows for multi-agent reasoning, GPT-4o synthesis, and vector embeddings.
                      </p>
                    </div>

                    <div style={{ padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: '6px' }}>
                      <Badge variant="warning">Retrieval (Staged)</Badge>
                      <h4 style={{ margin: '0.5rem 0' }}>Azure AI Search</h4>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        Hybrid vector & keyword index for engineering documentation and CAD part attributes.
                      </p>
                    </div>
                  </div>
                </Card>

                <Card title="Data Ingestion & Pipelines">
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    Original documents are staged in <code>data/documents/</code> and parsed text, CAD part hierarchies,
                    and chunk embeddings are persisted in <code>data/processed/</code>. The CLI runner in
                    <code>scripts/ingest_cad_docs.py</code> orchestrates batch processing.
                  </p>
                </Card>
              </div>
            );
          default:
            return <ChatWindow />;
        }
      }}
    </MainLayout>
  );
};

export default App;
