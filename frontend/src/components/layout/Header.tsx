import React, { useEffect, useState, useRef } from 'react';
import { agentService } from '../../services/agentService';

export type ActiveTab = 'chat' | 'documents' | 'cad' | 'architecture';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(false);
  const popoverRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setShowDetails(false);
      }
    };
    if (showDetails) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDetails]);

  return (
    <header className="header-bar">
      <div className="header-inner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div className="brand-mark">
            <span>Engineering Copilot</span>
            <span className="brand-badge">M10</span>
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
              CAD Attributes (Planned)
            </button>
            <button
              className={`nav-link ${activeTab === 'architecture' ? 'active' : ''}`}
              onClick={() => onTabChange('architecture')}
            >
              Architecture
            </button>
          </nav>
        </div>

        <div className="status-indicator-wrapper" ref={popoverRef}>
          {apiOnline === null ? (
            <div className="status-indicator">
              <span className="status-dot">○</span>
              <span>Connecting</span>
            </div>
          ) : apiOnline ? (
            <div className="status-indicator">
              <span className="status-dot">●</span>
              <span>API Available</span>
            </div>
          ) : (
            <div className="status-indicator-offline-group">
              <button
                type="button"
                className="status-indicator status-indicator-btn"
                onClick={() => setShowDetails((prev) => !prev)}
                aria-expanded={showDetails}
                title="Frontend deployed on Azure Static Web Apps · Backend available locally/Docker"
              >
                <span className="status-dot">○</span>
                <span>Live Preview</span>
              </button>

              <a
                href="https://github.com/chargedleo/engineering-document-copilot#readme"
                target="_blank"
                rel="noreferrer"
                className="status-run-locally-btn"
                title="View local/Docker run instructions in README"
              >
                Run locally →
              </a>

              {showDetails && (
                <div className="status-popover">
                  <div className="status-popover-header">
                    <span className="status-dot">○</span>
                    <span>Live Preview</span>
                  </div>
                  <p className="status-popover-desc">
                    The frontend is deployed on Azure. The engineering copilot backend is available for local/Docker execution.
                  </p>
                  <div className="status-popover-meta">
                    <div><strong>Frontend:</strong> Deployed on Azure Static Web Apps</div>
                    <div><strong>Backend:</strong> Available locally/Docker</div>
                  </div>
                  <div className="status-popover-actions">
                    <a
                      href="https://github.com/chargedleo/engineering-document-copilot#readme"
                      target="_blank"
                      rel="noreferrer"
                      className="btn-primary"
                      style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem', textDecoration: 'none' }}
                    >
                      Run locally →
                    </a>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem' }}
                      onClick={() => {
                        onTabChange('architecture');
                        setShowDetails(false);
                      }}
                    >
                      View Architecture
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
