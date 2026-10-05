import React from 'react';

export type ActiveTab = 'chat' | 'documents' | 'cad' | 'architecture';

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span style={{ fontSize: '1.25rem' }}>📐</span>
        <span>CAD Copilot</span>
      </div>
      <nav className="sidebar-nav">
        <button
          className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => onTabChange('chat')}
        >
          <span>💬</span>
          <span>Copilot Chat</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => onTabChange('documents')}
        >
          <span>📄</span>
          <span>Documents & Specs</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'cad' ? 'active' : ''}`}
          onClick={() => onTabChange('cad')}
        >
          <span>🧊</span>
          <span>CAD Models & BOM</span>
        </button>

        <button
          className={`nav-item ${activeTab === 'architecture' ? 'active' : ''}`}
          onClick={() => onTabChange('architecture')}
        >
          <span>🏗️</span>
          <span>Architecture Info</span>
        </button>
      </nav>
      <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <p>Backend: FastAPI (Async)</p>
        <p>Storage: PostgreSQL + Azure AI</p>
      </div>
    </aside>
  );
};
