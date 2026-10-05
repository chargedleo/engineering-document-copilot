import React, { useEffect, useState } from 'react';
import { agentService } from '../../services/agentService';

export type ActiveTab = 'chat' | 'documents' | 'cad' | 'architecture';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      const isHealthy = await agentService.checkHealth();
      if (mounted) {
        setApiOnline(isHealthy);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="header-bar">
      <div className="header-inner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div className="brand-mark">
            <span>Engineering Copilot</span>
            <span className="brand-badge">M7</span>
          </div>

          <nav className="nav-links">
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
        </div>

        <div className="status-indicator">
          {apiOnline === null ? (
            <>
              <span className="status-dot">○</span>
              <span>Connecting</span>
            </>
          ) : apiOnline ? (
            <>
              <span className="status-dot">●</span>
              <span>API Available</span>
            </>
          ) : (
            <>
              <span className="status-dot">○</span>
              <span>API Unavailable</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
