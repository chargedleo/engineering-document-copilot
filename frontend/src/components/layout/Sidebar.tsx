import React from 'react';
import { ActiveTab } from './Header';

export type { ActiveTab };

interface SidebarProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside style={{ borderRight: '1px solid var(--border-subtle)', padding: '1rem', width: '220px' }}>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button
          className={`nav-link ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => onTabChange('chat')}
        >
          Workspace
        </button>
        <button
          className={`nav-link ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => onTabChange('documents')}
        >
          Document Registry
        </button>
        <button
          className={`nav-link ${activeTab === 'cad' ? 'active' : ''}`}
          onClick={() => onTabChange('cad')}
        >
          CAD Attributes
        </button>
        <button
          className={`nav-link ${activeTab === 'architecture' ? 'active' : ''}`}
          onClick={() => onTabChange('architecture')}
        >
          Architecture
        </button>
      </nav>
    </aside>
  );
};
